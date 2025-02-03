import gradio as gr
import PyPDF2


# Abstract LLM integration function
def call_llm(cv_text, job_description):
    prompt = f"CV: {cv_text}\nJob Description: {job_description}\nPlease write a cover letter."
    # Replace this dummy response with an actual LLM API call.
    return "This is the generated cover letter based on your CV and job description."


def extract_text_from_pdf(pdf_file):
    reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text


def generate_cover_letter(cv_pdf, job_description, history, history_index):
    if cv_pdf is None:
        return "Please upload a CV PDF.", history, history_index
    cv_text = extract_text_from_pdf(cv_pdf.name)
    new_letter = call_llm(cv_text, job_description)
    # If there are undone versions, discard them
    if history_index < len(history) - 1:
        history = history[:history_index + 1]
    history.append(new_letter)
    history_index = len(history) - 1
    return new_letter, history, history_index


def undo_letter(current, history, history_index):
    if history_index > 0:
        history_index -= 1
    return history[history_index], history, history_index


def redo_letter(current, history, history_index):
    if history_index < len(history) - 1:
        history_index += 1
    return history[history_index], history, history_index


with gr.Blocks() as demo:
    gr.Markdown("## Cover Letter Generator")
    cv_pdf = gr.File(label="Upload CV PDF", file_types=[".pdf"])
    job_description = gr.Textbox(label="Job Description", lines=10)
    cover_letter = gr.Textbox(label="Cover Letter", lines=15)
    history_state = gr.State([])  # List to store cover letter versions
    history_index_state = gr.State(-1)  # Pointer to the current version

    with gr.Row():
        generate_btn = gr.Button("Generate Cover Letter")
        undo_btn = gr.Button("Undo")
        redo_btn = gr.Button("Redo")

    generate_btn.click(
        generate_cover_letter,
        inputs=[cv_pdf, job_description, history_state, history_index_state],
        outputs=[cover_letter, history_state, history_index_state]
    )
    undo_btn.click(
        undo_letter,
        inputs=[cover_letter, history_state, history_index_state],
        outputs=[cover_letter, history_state, history_index_state]
    )
    redo_btn.click(
        redo_letter,
        inputs=[cover_letter, history_state, history_index_state],
        outputs=[cover_letter, history_state, history_index_state]
    )

demo.launch()
