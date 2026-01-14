import spacy
from spacy.matcher import Matcher, PhraseMatcher
import re
import asyncio
import threading
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor
import functools

class AsyncPropertyQueryParser:
    """
    Async-optimized property query parser for high-traffic environments
    Uses thread pool for CPU-bound spaCy operations to avoid blocking event loop
    """
    
    # Class-level variables to avoid repeated initialization
    _nlp = None
    _matcher = None
    _phrase_matcher = None
    _kenyan_locations = None
    _kenyan_universities = None
    _initialized = False
    _lock = threading.Lock()
    
    # Thread pool for CPU-bound operations
    _thread_pool = ThreadPoolExecutor(max_workers=4)
    
    @classmethod
    def initialize_parser(cls):
        """Initialize parser once (thread-safe)"""
        with cls._lock:
            if not cls._initialized:
                cls._nlp = spacy.load("en_core_web_sm")
                cls._matcher = Matcher(cls._nlp.vocab)
                cls._phrase_matcher = PhraseMatcher(cls._nlp.vocab, attr="LOWER")
                
                # Common Kenyan locations and universities
                cls._kenyan_locations = {
                    'nairobi', 'mombasa', 'kisumu', 'nakuru', 'eldoret', 'thika', 'malindi', 
                    'lamu', 'naivasha', 'kakamega', 'kisii', 'nyeri', 'meru', 'garissa',
                    'westlands', 'kileleshwa', 'lavington', 'kilimani', 'karen', 'rongai'
                }
                
                cls._kenyan_universities = {
                    'university of nairobi', 'kenyatta university', 'moi university', 'jkuat',
                    'strathmore university', 'mount kenya university', 'technical university',
                    'murang\'a university', 'kisumu university', 'maseno university', 'jkuat'
                }
                
                cls._initialize_matchers()
                cls._initialized = True
    
    @classmethod
    def _initialize_matchers(cls):
        """Initialize all matchers with comprehensive patterns"""
        
        # Enhanced Price patterns
        price_patterns = [
            [{"LOWER": {"IN": ["cheap", "affordable", "budget", "inexpensive", "low-cost", "economical"]}}],
            [{"LOWER": "under"}, {"LIKE_NUM": True}],
            [{"LOWER": "less"}, {"LOWER": "than"}, {"LIKE_NUM": True}],
            [{"LOWER": "below"}, {"LIKE_NUM": True}],
            [{"LOWER": "maximum"}, {"LIKE_NUM": True}],
            [{"LOWER": "max"}, {"LIKE_NUM": True}],
            [{"LOWER": {"IN": ["ksh", "shilling", "dollar", "usd"]}}, {"LIKE_NUM": True}],
            [{"LIKE_NUM": True}, {"LOWER": {"IN": ["ksh", "shilling", "dollar", "usd", "k"]}}],
            [{"LOWER": "price"}, {"LOWER": "range"}, {"LIKE_NUM": True}, {"LOWER": "to"}, {"LIKE_NUM": True}],
        ]
        cls._matcher.add("PRICE", price_patterns)
        
        # Enhanced Room type patterns
        room_patterns = [
            [{"LIKE_NUM": True}, {"LOWER": {"IN": ["bed", "bedroom", "bedrooms", "br"]}}],
            [{"LIKE_NUM": True}, {"LOWER": {"IN": ["bath", "bathroom", "bathrooms", "ba"]}}],
            [{"LOWER": {"IN": ["studio", "studio apartment", "bedsitter", "bedsitter"]}}],
            [{"LOWER": "single"}, {"LOWER": {"IN": ["room", "bedroom", "apartment"]}}],
            [{"LOWER": "double"}, {"LOWER": {"IN": ["room", "bedroom", "apartment"]}}],
            [{"LOWER": "one"}, {"LOWER": "bedroom"}],
            [{"LOWER": "two"}, {"LOWER": "bedroom"}],
            [{"LOWER": "three"}, {"LOWER": "bedroom"}],
            [{"LOWER": "self"}, {"LOWER": "contained"}],
            [{"LOWER": "bachelor"}],
        ]
        cls._matcher.add("ROOM_TYPE", room_patterns)
        
        # Enhanced Location patterns
        location_patterns = [
            [{"LOWER": {"IN": ["near", "close", "around", "beside", "next", "adjacent"]}}, 
             {"POS": {"IN": ["NOUN", "PROPN"]}}],
            [{"LOWER": {"IN": ["near", "close", "around", "beside", "next", "adjacent"]}}, 
             {"POS": {"IN": ["NOUN", "PROPN"]}}, {"POS": {"IN": ["NOUN", "PROPN"]}}],
            [{"LOWER": {"IN": ["in", "at", "within", "inside"]}}, {"ENT_TYPE": "GPE"}],
            [{"LOWER": {"IN": ["in", "at", "within", "inside"]}}, {"POS": "PROPN"}],
            [{"LOWER": "location"}, {"LOWER": "in"}, {"ENT_TYPE": "GPE"}],
            [{"LOWER": "situated"}, {"LOWER": "in"}, {"ENT_TYPE": "GPE"}],
        ]
        cls._matcher.add("LOCATION", location_patterns)
        
        # Property type patterns
        property_patterns = [
            [{"LOWER": {"IN": ["house", "apartment", "flat", "condo", "villa", "mansion", "cottage"]}}],
            [{"LOWER": "rental"}, {"LOWER": "house"}],
            [{"LOWER": "family"}, {"LOWER": "house"}],
        ]
        cls._matcher.add("PROPERTY_TYPE", property_patterns)
        
        # Features/Amenities with phrase matching
        amenities_list = [
            "wifi", "wi-fi", "wireless", "internet", "broadband",
            "parking", "garage", "car park", "off-street parking",
            "pool", "swimming pool", "jacuzzi",
            "garden", "balcony", "terrace", "patio",
            "furnished", "unfurnished", "semi-furnished",
            "air conditioning", "ac", "heating", "cooling",
            "security", "cctv", "alarm", "gated community",
            "pet friendly", "pets allowed", "elevator", "lift",
            "laundry", "washing machine", "dryer",
            "kitchen", "modern kitchen", "equipped kitchen"
        ]
        amenity_patterns = [cls._nlp.make_doc(amenity) for amenity in amenities_list]
        cls._phrase_matcher.add("AMENITY", amenity_patterns)

    @staticmethod
    def _extract_with_regex(text: str) -> Dict[str, Any]:
        """Enhanced regex extraction with better patterns"""
        text_lower = text.lower()
        entities = {}
        
        # Enhanced bedroom extraction
        bedroom_patterns = [
            r'(\d+)\s*(?:bed|bedroom|br|beds)\b',
            r'\b(one|two|three|four|five|six|seven|eight|nine|ten)\s+(?:bed|bedroom|br)\b',
            r'\b(studio|bedsitter|bachelor)\b',
            r'\b(single|double)\s+(?:room|bedroom)\b'
        ]
        
        for pattern in bedroom_patterns:
            match = re.search(pattern, text_lower)
            if match:
                if match.group(1).isdigit():
                    entities['bedrooms'] = int(match.group(1))
                elif match.group(1) in ['studio', 'bedsitter', 'bachelor', 'single']:
                    entities['bedrooms'] = 1
                    entities['room_type'] = match.group(1)
                elif match.group(1) == 'double':
                    entities['bedrooms'] = 2
                    entities['room_type'] = 'double'
                elif match.group(1) in ['one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten']:
                    number_words = {'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5, 
                                  'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10}
                    entities['bedrooms'] = number_words[match.group(1)]
                break
        
        # Enhanced bathroom extraction
        bathroom_match = re.search(r'(\d+)\s*(?:bath|bathroom|bathrooms|ba)\b', text_lower)
        if bathroom_match:
            entities['bathrooms'] = int(bathroom_match.group(1))
        
        # Enhanced price extraction
        price_patterns = [
            r'(?:under|less than|below|maximum|max)\s*[\$]?\s*(\d+[,\d]*)',
            r'[\$]?\s*(\d+[,\d]*)\s*(?:ksh|shilling|dollar|usd|k)\b',
            r'price\s*range?\s*(\d+)\s*to\s*(\d+)',
            r'(\d+)\s*-\s*(\d+)\s*(?:ksh|shilling)'
        ]
        
        for pattern in price_patterns:
            match = re.search(pattern, text_lower)
            if match:
                if 'to' in pattern or '-' in pattern:
                    entities['price_range'] = f"{match.group(1)}-{match.group(2)}"
                elif 'under' in pattern or 'below' in pattern or 'maximum' in pattern:
                    entities['max_price'] = match.group(1).replace(',', '')
                else:
                    entities['price'] = match.group(1).replace(',', '')
                break
        
        return entities

    @classmethod
    def _extract_locations(cls, doc) -> Dict[str, Any]:
        """Enhanced location extraction with better boundary detection"""
        locations = {}
        text_lower = doc.text.lower()
        
        # Extract entities using spaCy NER first
        for ent in doc.ents:
            if ent.label_ in ["GPE", "LOC", "FAC", "ORG"] and len(ent.text) > 2:
                location_text = ent.text.lower()
                
                # Check if it's a Kenyan location
                if location_text in cls._kenyan_locations:
                    locations['city'] = location_text
                # Check if it's a university
                elif any(uni in location_text for uni in cls._kenyan_universities):
                    locations['landmark'] = location_text
                    locations['location_type'] = 'university'
                else:
                    locations['area'] = location_text
        
        # Enhanced "near" detection with proper boundaries
        near_patterns = [
            r'near\s+([^,.\n]+?)(?:\s+with|\s+and|\s+under|\s+for|\s+having|,|\.|$)',
            r'close to\s+([^,.\n]+?)(?:\s+with|\s+and|\s+under|\s+for|\s+having|,|\.|$)',
            r'around\s+([^,.\n]+?)(?:\s+with|\s+and|\s+under|\s+for|\s+having|,|\.|$)',
            r'next to\s+([^,.\n]+?)(?:\s+with|\s+and|\s+under|\s+for|\s+having|,|\.|$)',
            r'beside\s+([^,.\n]+?)(?:\s+with|\s+and|\s+under|\s+for|\s+having|,|\.|$)'
        ]
        
        for pattern in near_patterns:
            match = re.search(pattern, text_lower)
            if match:
                landmark = match.group(1).strip()
                landmark = re.sub(r'\s+(with|and|under|for|having).*$', '', landmark).strip()
                if landmark and len(landmark) > 2:
                    locations['near'] = landmark
                    locations['location_relation'] = 'near'
                    break
        
        # Extract "in" location with proper boundaries
        in_patterns = [
            r'in\s+([^,.\n]+?)(?:\s+with|\s+and|\s+under|\s+for|\s+having|,|\.|$)',
            r'at\s+([^,.\n]+?)(?:\s+with|\s+and|\s+under|\s+for|\s+having|,|\.|$)',
            r'within\s+([^,.\n]+?)(?:\s+with|\s+and|\s+under|\s+for|\s+having|,|\.|$)'
        ]
        
        for pattern in in_patterns:
            match = re.search(pattern, text_lower)
            if match:
                city_area = match.group(1).strip()
                city_area = re.sub(r'\s+(with|and|under|for|having).*$', '', city_area).strip()
                if city_area and len(city_area) > 2:
                    locations['in'] = city_area
                    locations['location_relation'] = 'in'
                    break
        
        return locations

    @staticmethod
    def _extract_room_types(doc) -> Dict[str, Any]:
        """Enhanced room type detection"""
        room_info = {}
        text = doc.text.lower()
        
        room_type_patterns = {
            'studio': r'\b(studio|bedsitter|bachelor)\b',
            'single': r'\bsingle\s+(?:room|bedroom)\b',
            'double': r'\bdouble\s+(?:room|bedroom)\b',
            'one_bedroom': r'\bone\s+bedroom\b',
            'two_bedroom': r'\btwo\s+bedroom\b',
            'three_bedroom': r'\bthree\s+bedroom\b',
            'self_contained': r'\bself\s+contained\b'
        }
        
        for room_type, pattern in room_type_patterns.items():
            if re.search(pattern, text):
                if room_type == 'studio':
                    room_info['room_type'] = 'studio'
                    room_info['bedrooms'] = 1
                elif room_type == 'single':
                    room_info['room_type'] = 'single'
                    room_info['bedrooms'] = 1
                elif room_type == 'double':
                    room_info['room_type'] = 'double'
                    room_info['bedrooms'] = 2
                elif room_type == 'one_bedroom':
                    room_info['bedrooms'] = 1
                elif room_type == 'two_bedroom':
                    room_info['bedrooms'] = 2
                elif room_type == 'three_bedroom':
                    room_info['bedrooms'] = 3
                elif room_type == 'self_contained':
                    room_info['room_type'] = 'self contained'
                break
        
        return room_info

    @classmethod
    def _parse_query_sync(cls, text: str) -> Dict[str, Any]:
        """Synchronous parsing function to run in thread pool"""
        if not cls._initialized:
            cls.initialize_parser()
            
        doc = cls._nlp(text.lower())
        entities = {}
        
        # Extract using multiple methods
        regex_entities = cls._extract_with_regex(text)
        location_entities = cls._extract_locations(doc)
        room_entities = cls._extract_room_types(doc)
        
        # Combine all entities
        entities.update(regex_entities)
        entities.update(location_entities)
        entities.update(room_entities)
        
        # Process with matchers
        matches = cls._matcher(doc)
        phrase_matches = cls._phrase_matcher(doc)
        
        # Process standard matcher
        for match_id, start, end in matches:
            rule_name = cls._nlp.vocab.strings[match_id]
            span = doc[start:end]
            
            if rule_name == "PRICE" and 'price' not in entities and 'max_price' not in entities:
                entities['price_indicator'] = span.text
            elif rule_name == "ROOM_TYPE" and 'bedrooms' not in entities:
                num_match = re.search(r'(\d+)', span.text)
                if num_match:
                    entities['bedrooms'] = int(num_match.group(1))
            elif rule_name == "PROPERTY_TYPE":
                entities['property_type'] = span.text
        
        # Process amenities
        amenities = []
        for match_id, start, end in phrase_matches:
            amenity = doc[start:end].text
            if amenity in ['wi-fi', 'wireless', 'broadband']:
                amenity = 'wifi'
            elif amenity in ['garage', 'car park', 'off-street parking']:
                amenity = 'parking'
            elif amenity == 'ac':
                amenity = 'air conditioning'
            elif amenity == 'lift':
                amenity = 'elevator'
            elif amenity == 'pets allowed':
                amenity = 'pet friendly'
            
            if amenity not in amenities:
                amenities.append(amenity)
        
        if amenities:
            entities['amenities'] = amenities
        
        return cls._clean_entities(entities)

    @staticmethod
    def _clean_entities(entities: Dict[str, Any]) -> Dict[str, Any]:
        """Clean and normalize final entities"""
        cleaned = {}
        
        for key, value in entities.items():
            if value is not None and value != '' and value != []:
                cleaned[key] = value
        
        if 'max_price' in cleaned and 'price' not in cleaned:
            cleaned['price_range'] = f"under {cleaned['max_price']}"
        
        # Clean location data
        if 'city' in cleaned:
            cleaned['location'] = cleaned['city']
        elif 'landmark' in cleaned:
            cleaned['location'] = cleaned['landmark']
        elif 'area' in cleaned:
            cleaned['location'] = cleaned['area']
        elif 'near' in cleaned:
            cleaned['location'] = cleaned['near']
            cleaned['proximity'] = 'near'
        elif 'in' in cleaned:
            cleaned['location'] = cleaned['in']
        
        for field in ['near', 'in', 'price_indicator']:
            cleaned.pop(field, None)
        
        return cleaned

    @classmethod
    async def parse_query(cls, text: str) -> Dict[str, Any]:
        """
        Async method to parse query - runs CPU-bound operations in thread pool
        """
        if not cls._initialized:
            cls.initialize_parser()
            
        # Run the CPU-intensive parsing in thread pool
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            cls._thread_pool, 
            cls._parse_query_sync, 
            text
        )
        return result

    @classmethod
    async def parse_multiple_queries(cls, queries: List[str]) -> List[Dict[str, Any]]:
        """
        Parse multiple queries concurrently for better throughput
        """
        if not cls._initialized:
            cls.initialize_parser()
            
        tasks = [cls.parse_query(query) for query in queries]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle any exceptions
        processed_results = []
        for result in results:
            if isinstance(result, Exception):
                # Log error and return empty dict
                processed_results.append({})
            else:
                processed_results.append(result)
                
        return processed_results

    @classmethod
    def shutdown(cls):
        """Cleanup thread pool"""
        if cls._thread_pool:
            cls._thread_pool.shutdown(wait=True)


# FastAPI/Async compatible usage
async def get_query_parser(search_query: str) -> dict:
    """
    Main async endpoint for query parsing
    """
    try:
        entities = await AsyncPropertyQueryParser.parse_query(search_query)
        return {
            "success": True,
            "query": search_query,
            "entities": entities,
            "timestamp": asyncio.get_event_loop().time()
        }
    except Exception as e:
        return {
            "success": False,
            "query": search_query,
            "error": str(e),
            "entities": {}
        }


async def batch_parse_queries(queries: List[str]) -> List[dict]:
    """
    Batch parse multiple queries efficiently
    """
    try:
        results = await AsyncPropertyQueryParser.parse_multiple_queries(queries)
        return [
            {
                "success": True,
                "query": query,
                "entities": entities,
                "timestamp": asyncio.get_event_loop().time()
            }
            for query, entities in zip(queries, results)
        ]
    except Exception as e:
        return [
            {
                "success": False,
                "query": query,
                "error": str(e),
                "entities": {}
            }
            for query in queries
        ]



# Test function
# async def test_async_parser():
#     """Test the async parser"""
#     test_queries = [
#         "find affordable rooms near Kisumu with Wi-Fi",
#         "I need 2 bedroom apartment with parking and pool under 25000 KSH",
#         "looking for cheap studio near university with internet",
#         "3 bedroom house with garden and parking in Nairobi",
#     ]
    
#     print("=== ASYNC PROPERTY QUERY PARSER RESULTS ===")
    
#     result = await get_query_parser(test_queries[0])
#     print(f"Single query result: {result}")
    
#     batch_results = await batch_parse_queries(test_queries)
#     for i, result in enumerate(batch_results):
#         print(f"Query {i+1}: {result['query']}")
#         print(f"Entities: {result['entities']}")
#         print("-" * 50)

# if __name__ == "__main__":
#     # Run test
#     asyncio.run(test_async_parser())


#FOR SEARCHING TO WORK
# python -m spacy download en_core_web_sm 
# or
# import spacy.cli
# spacy.cli.download("en_core_web_sm")