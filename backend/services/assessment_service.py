from __future__ import annotations


DEFAULT_QUESTIONS = [
    {"question": "Which library is widely used for tabular data in Python?", "options": ["NumPy", "Pandas", "Flask", "Pygame"], "answer": "Pandas", "skill": "Python"},
    {"question": "Which SQL clause filters rows?", "options": ["GROUP BY", "WHERE", "ORDER BY", "AS"], "answer": "WHERE", "skill": "SQL"},
    {"question": "Which chart compares categories most directly?", "options": ["Bar chart", "Scatter only", "Map only", "Gauge only"], "answer": "Bar chart", "skill": "Data Visualization"},
    {"question": "What does KPI stand for?", "options": ["Key Performance Indicator", "Known Python Interface", "Kernel Process Index", "Key Program Input"], "answer": "Key Performance Indicator", "skill": "Data Analysis"},
    {"question": "Which measure is a common average?", "options": ["Mean", "Mode only", "Range only", "Count only"], "answer": "Mean", "skill": "Statistics"},
]


def grade_answers(questions, answers, passing_score=60) -> dict:
    correct = [question for question, answer in zip(questions, answers) if answer == question["answer"]]
    score = round(len(correct) / max(1, len(questions)) * 100)
    demonstrated = [question["skill"] for question in correct]
    improvement = [question["skill"] for question, answer in zip(questions, answers) if answer != question["answer"]]
    return {"score": score, "passed": score >= passing_score, "demonstrated": demonstrated, "improvement": improvement}