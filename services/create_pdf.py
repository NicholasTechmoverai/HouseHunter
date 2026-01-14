from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

file_path = "ML_Roadmap_Flowchart.pdf"

c = canvas.Canvas(file_path, pagesize=A4)
width, height = A4

c.setFont("Helvetica-Bold", 18)
c.drawCentredString(width / 2, height - 50,
                    "Machine Learning Programmer → Engineer Roadmap")

c.setFont("Helvetica", 12)
y = height - 100

steps = [
    "Start",
    "Learn Python (Syntax, NumPy, Pandas)",
    "Math Foundations (Linear Algebra, Probability, Statistics)",
    "Core Machine Learning (Regression, Trees, Clustering)",
    "Model Evaluation & Feature Engineering",
    "Projects & Kaggle Practice",
    "Deep Learning (CNNs, NLP, Transformers)",
    "ML Engineering (APIs, Docker, Cloud)",
    "MLOps (Monitoring, CI/CD, Versioning)",
    "Advanced Topics (LLMs, RL, Recommenders)",
    "Machine Learning Engineer"
]

for step in steps:
    c.drawCentredString(width / 2, y, step)
    y -= 35

c.save()

print("PDF created:", file_path)
