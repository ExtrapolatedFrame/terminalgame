# questions file
questions = [
    {
        "question": "{a} + {b} * {c} = ?",
        "answer": lambda a, b, c: a + b * c,
        "type": "math",
        "weight": 1,
    }, {
        "question": "{a} * ({b} + {c}) / 2 = ?",
        "answer": lambda a, b, c: a * (b + c) * 0.5,
        "type": "math",
        "weight": 1,
    }, {
            "question": "{a} * {b} - {c} = ?",
            "answer": lambda a, b, c: a * b - c,
            "type": "math",
            "weight": 1,
        },

    
    
]