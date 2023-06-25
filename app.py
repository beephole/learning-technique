from apikey import apikey
import pandas as pd
import streamlit as st
from langchain.llms import OpenAI
import openai,os,ast,json,base64
from weasyprint import HTML
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain, SequentialChain
from langchain.memory import ConversationBufferMemory
from langchain.utilities import WikipediaAPIWrapper

os.environ["OPENAI_API_KEY"] = apikey

# App 
st.title("🗃️💭 Memory Palace Creator")
prompt = st.text_input(
    "Enter the lines of code you want to memorize (separated by new lines)"
)

# Prompt template
memory_palace_template = PromptTemplate(
    input_variables=["lines_of_code"],
    template='Please create a cohesive or fictional and interconnected memory palace story in english grammar to help memorize the following lines of code:\n{lines_of_code}\nFor each line, provide a short description of its function, embed it into the story by illustrating with real life scenarios so that it naturally flows and connects to the previous and next lines, and provide a proffesional detailed image prompt based on story for creating an image with the DALL-E API, Response must be a list of python dictionaries with no help description,use double quotes ,fix all syntax erros and dont use single apostrophs inside values or special chars , and make it a valid list of python dictionares so it never pulls SyntaxError,use  these keys for every dict - codeLine , codeDescription , story , imagePrompt.',
)

# Memory
memory_palace_memory = ConversationBufferMemory(
    input_key="lines_of_code", memory_key="chat_history"
)

# Llms
llm = OpenAI(temperature=0.9,max_tokens=2000)
memory_palace_chain = LLMChain(
    llm=llm,
    prompt=memory_palace_template,
    verbose=True,
    output_key="memory_palace",
    memory=memory_palace_memory,
)

def create_html_table(data_frame):
    table_html = '<table border="1" cellpadding="5" cellspacing="0">'

    # Add table headers
    table_html += '<tr>'
    for column in data_frame.columns:
        table_html += f'<th>{column.capitalize()}</th>'
    table_html += '</tr>'

    # Add table rows
    for _, row in data_frame.iterrows():
        table_html += '<tr>'
        for column in data_frame.columns:
            if column == "imageUrl":
                table_html += f'<td><img src="{row[column]}" width="100" /></td>'
            else:
                table_html += f'<td>{row[column]}</td>'
        table_html += '</tr>'

    table_html += '</table>'
    return table_html

def generateimg(prompt):
    response = openai.Image.create(prompt="Eye-catching and vivid image of " + prompt + " with a perfect mix of photorealism and captivating, Blender-style animation effects. The image should evoke a sense of wonder and be memorable, containing balanced visual elements without excessive messiness or clutter.", n=1, size="1024x1024")
    return response["data"][0]["url"]

def get_csv_download_link(data_frame, file_name):
    csv_data = data_frame.to_csv(index=False)
    binary_data = base64.b64encode(csv_data.encode()).decode()
    href = f'<a href="data:file/csv;base64,{binary_data}" download="{file_name}.csv">Download CSV</a>'
    return href

def create_pdf_from_html(html_table, file_name,title="Memory Palace Story by A.F"):
    # Add CSS 
    styles = '''
    <style>
        @page { size: A4 landscape; margin: 1cm; }
        body { font-family: Arial, sans-serif; font-size: 11pt; }
        table { border-collapse: collapse; width: 100%; page-break-inside: auto; }
        tr { page-break-inside: avoid; }
        th, td { border: 1px solid black; padding: 5px; text-align: left; }
        th { background-color: #f1f1f1; }
        img { width: 100px; }
    </style>
    '''
    title_html = f'<h1 style="text-align: center;">{title}</h1>'
    html_with_title_and_styles = styles + title_html + html_table
    # Generate the PDF
    pdf_bytes = HTML(string=html_with_title_and_styles).write_pdf()
    base64_enc = base64.b64encode(pdf_bytes).decode()
    return f'<a href="data:application/pdf;base64,{base64_enc}" download="{file_name}.pdf">Download PDF</a>'



if prompt:
    # Convert lines of code to a format suitable for LLMChain input
    replace_quotes = lambda line: line.strip().replace('"' ,"'")

# Convert lines of code to a format suitable for LLMChain input
    formatted_code = "\n".join(["- " + replace_quotes(line) for line in prompt.strip().split("\n")])

    # Generate the memory palace story
    memory_palace_response = memory_palace_chain.run(lines_of_code=formatted_code)
    if  memory_palace_response:
        st.write("Generation Completing ...")
    list_of_dictionaries = ast.literal_eval(memory_palace_response)

    # Generate images for each image prompt using DALL-E
    for dictionary in list_of_dictionaries:
        image_url = generateimg(
            dictionary["imagePrompt"]
        )  # Replace with your DALL-E function call
        dictionary["imageUrl"] = image_url


    data_frame = pd.DataFrame(list_of_dictionaries)
    html_table = create_html_table(data_frame)

    with st.expander("Memory Palace Table"):
    # Display the HTML table
        st.write(html_table, unsafe_allow_html=True)
        st.markdown(get_csv_download_link(data_frame, "memory_palace_story"), unsafe_allow_html=True)
        pdf_download_link = create_pdf_from_html(html_table, "memory_palace_story")
        st.markdown(pdf_download_link, unsafe_allow_html=True)
  


    #with st.expander("Memory Palace Story"):
     #   st.table(data_frame)
    count=1
    
    st.markdown(
        f'<p style="color:grey;font-size:1.8em;text-align: center;">Memory Palace Story by A.F</p>',
        unsafe_allow_html=True,
    )
    for dictionary in list_of_dictionaries:
        st.markdown(
            f'<p style="color:grey;font-size:1.5em;text-align: center;">Line of Code</p>',
            unsafe_allow_html=True,
        )
        st.code(dictionary["codeLine"])

        st.markdown(
        '<p style="color:green; font-size:1.5em;text-align: center;"><b>Code Description</b></p>',
        unsafe_allow_html=True,
        )
        st.write(dictionary["codeDescription"])
        st.markdown(
        '<p style="color:green; font-size:1.5em;text-align: center;"><b>Story</b></p>',
        unsafe_allow_html=True,
        )
        st.write(dictionary["story"])
        st.markdown(
        '<p style="color:yellow; font-size:1.5em;text-align: center;"><b>Generated Image </b></p>',
        unsafe_allow_html=True,
        )
        st.markdown(
            f'<p style="color:yellow;">{dictionary["imagePrompt"]}</p>',
            unsafe_allow_html=True,
        )
        st.image(dictionary["imageUrl"])
        st.markdown(
            f'<p style="color:grey;font-size:0.8em;text-align: left;">Page {count}</p>',
            unsafe_allow_html=True,
        )
            
        st.markdown("<hr/>", unsafe_allow_html=True)
        count+=1

    with st.expander("History"):
        st.info(memory_palace_memory.buffer)

    
