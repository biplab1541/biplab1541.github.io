import os
from dotenv import load_dotenv
from flask import Flask, request, render_template
import requests
from langchain_community.llms import Ollama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Load environment variables
load_dotenv()

# Flask application setup
app = Flask(__name__)

# Function to get data from the Materials Project API
def get_material_data(material_id):
    url = f"https://materialsproject.org/rest/v2/materials/{material_id}"
    headers = {
        "Authorization": f"Bearer {os.getenv('MATERIALS_PROJECT_API_KEY')}"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()  # Return the JSON response
    else:
        return {"error": f"Unable to fetch material data. Status code: {response.status_code}"}

# Chatbot initialization
def initialize_chatbot():
    # Chat prompt for the chatbot
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "Provide expert responses to user queries, focusing on materials science."),
            ("user", "Question: {question}")
        ]
    )
    
    # Initialize Llama 3.2:1b using Ollama and output parser
    llm = Ollama(model="llama3.2:1b")
    output_parser = StrOutputParser()
    
    # Combine prompt, LLM, and parser into a chain
    chain = prompt | llm | output_parser
    return chain

# Initialize chatbot
chain = initialize_chatbot()

# Define home route
@app.route('/', methods=['GET', 'POST'])
def home():
    output = None
    input_text = None
    if request.method == 'POST':
        input_text = request.form['input_text']
        material_data = None

        # Check if the input is a material ID
        if input_text.startswith("mp-"):
            material_data = get_material_data(input_text)
        
        if material_data and "error" not in material_data:
            # Parse material data for rendering
            parsed_data = {
                "Material ID": material_data.get("response", {}).get("material_id", "N/A"),
                "Elements": material_data.get("response", {}).get("elements", []),
                "Density": material_data.get("response", {}).get("density", "N/A"),
            }
            output = parsed_data
        elif material_data and "error" in material_data:
            # Handle API errors
            output = {"Error": material_data["error"]}
        else:
            # Wrap chatbot response in a dictionary
            chatbot_response = chain.invoke({'question': input_text})
            output = {"Chatbot Response": chatbot_response}
    
    return render_template('index.html', input_text=input_text, output=output)

if __name__ == '__main__':
    app.run(debug=True)
