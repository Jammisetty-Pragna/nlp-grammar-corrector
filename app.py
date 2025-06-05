from flask import Flask, render_template, request, jsonify
import spacy
import language_tool_python

# Flask app initialization
app = Flask(__name__)

# Load spaCy's English model
nlp = spacy.load("en_core_web_sm")

# Initialize LanguageTool for grammar checking
tool = language_tool_python.LanguageTool('en-US')

def identify_nouns(text):
    """Identify all nouns and proper nouns in the text."""
    doc = nlp(text)
    return [token.text for token in doc if token.pos_ in ["NOUN", "PROPN"]]

def highlight_mistakes(text):
    """Highlight grammatical mistakes while preserving nouns."""
    nouns = identify_nouns(text)
    matches = tool.check(text)

    if not matches:
        return None

    highlighted_text = ""
    last_pos = 0

    for match in matches:
        start, end = match.offset, match.offset + match.errorLength
        original_text = text[start:end]

        # Skip highlighting if the word is a noun or proper noun
        if original_text in nouns:
            continue

        highlighted_text += text[last_pos:start]
        highlighted_text += f"<span style='color: red;'>{original_text}</span>"
        last_pos = end

    highlighted_text += text[last_pos:]
    return highlighted_text

def correct_sentence(text):
    """Correct grammar using LanguageTool while preserving nouns."""
    nouns = identify_nouns(text)
    matches = tool.check(text)

    if not matches:
        return None

    corrected_text = text

    for match in reversed(matches):
        start, end = match.offset, match.offset + match.errorLength
        original_text = text[start:end]

        # Skip corrections if the word is a noun or proper noun
        if original_text in nouns:
            continue

        suggestion = match.replacements[0] if match.replacements else original_text
        corrected_text = corrected_text[:start] + suggestion + corrected_text[end:]

    return corrected_text

@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/process', methods=['POST'])
def process():
    """Process user input and return highlighted and corrected text."""
    data = request.get_json()
    user_input = data.get('text')

    if not user_input:
        return jsonify({'error': 'No input text provided.'}), 400

    highlighted = highlight_mistakes(user_input)
    corrected = correct_sentence(user_input)

    if not highlighted and not corrected:
        return jsonify({'message': "<div style='color: blue; font-weight: bold; font-style: italic; text-align: center;'>No grammatical mistakes in the given text.</div>"})

    response = {}
    if highlighted:
        response['highlighted'] = highlighted
    if corrected:
        response['corrected'] = corrected

    return jsonify(response)

# Run the Flask app
if __name__ == '__main__':
    app.run(port=5000, debug=True)
