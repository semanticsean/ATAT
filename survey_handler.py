import random
import time
import logging 



def generate_random_answers(questions):
    answers = {}
    for question_id, question_info in questions.items():
        question_type = question_info['type']
        if question_type == 'multiple_choice':
            answers[question_id] = random.choice(question_info['options'])
        elif question_type == 'text_area':
            answers[question_id] = random.choice(['Yes', 'No', 'Maybe'])
        elif question_type == 'checkbox':
            answers[question_id] = random.choice([True, False])
        elif question_type == 'scale':
            answers[question_id] = random.randint(question_info['min'], question_info['max'])
        else:
            answers[question_id] = 'Unknown question type'
    return answers

def process_survey_responses(questions):
    responses = []
    for _ in range(5):
        response = generate_random_answers(questions)
        responses.append(response)
        time.sleep(0.1) 
    return responses

def extract_questions_from_form(form_data):
    questions = {}
    for key, value in form_data.items():
        if key.startswith('question_'):
            question_id = key.split('_')[1]
            question_type = form_data.get(f"question_{question_id}_type")
            questions[question_id] = {
                'type': question_type,
                'text': value
            }
            if question_type == 'multiple_choice':
                options = form_data.getlist(f"question_{question_id}_options")
                questions[question_id]['options'] = options
            elif question_type == 'scale':
                min_value = int(form_data.get(f"question_{question_id}_min"))
                max_value = int(form_data.get(f"question_{question_id}_max"))
                questions[question_id]['min'] = min_value
                questions[question_id]['max'] = max_value
    return questions

@property
def filename(self):
    # Example of deriving a filename from other attributes
    return f"{self.name}_{self.id}.json"