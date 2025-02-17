import gradio as gr
import requests
from services.cover_letter_generator import CoverLetterGenerator




# Initialize the Cover Letter Generator.
clg = CoverLetterGenerator()

# Get the list of model choices dynamically.
model_choices = clg.get_model_ids()

def generate_cover_letter(cv_file, job_description, history_state, dropdown):
    if cv_file is None:
        return "Please upload a CV first.", history_state, len(history_state) - 1

    try:
        # Pass the selected model (from dropdown) to the cover letter generator.
        cover_letter = clg.generate_cover_letter(cv_file.name, job_description, dropdown)
        new_history = history_state + [cover_letter]
        new_index = len(new_history) - 1
        return cover_letter, new_history, new_index
    except Exception as e:
        return f"Error: {str(e)}", history_state, len(history_state) - 1

def undo_action(current_cover_letter, history_state, history_index):
    if history_index > 0:
        new_index = history_index - 1
        return history_state[new_index], history_state, new_index
    else:
        return current_cover_letter, history_state, history_index

def redo_action(current_cover_letter, history_state, history_index):
    if history_index < len(history_state) - 1:
        new_index = history_index + 1
        return history_state[new_index], history_state, new_index
    else:
        return current_cover_letter, history_state, history_index

# Define the Gradio interface.
with gr.Blocks() as demo:
    gr.Markdown("# Cover Letter Generator")
    with gr.Row():
        with gr.Column():
            cv_input = gr.File(label="Upload your CV", file_types=[".docx", ".pdf"])
            job_description_input = gr.Textbox(label="Job Description", placeholder="Enter the job description here.")
            dropdown = gr.Dropdown(
                choices=model_choices,
                label="Select Model",
                value=model_choices[0] if model_choices else "deepseek-r1:32b"
            )
            generate_button = gr.Button("Generate Cover Letter")
        with gr.Column():
            with gr.Row():
                undo_button = gr.Button("Undo")
                redo_button = gr.Button("Redo")
            cover_letter_output = gr.Textbox(label="Generated Cover Letter", lines=25)
            history_state = gr.State(value=[])
            current_index = gr.State(value=-1)

    # Event handlers.
    generate_button.click(
        fn=generate_cover_letter,
        inputs=[cv_input, job_description_input, history_state, dropdown],
        outputs=[cover_letter_output, history_state, current_index]
    )

    undo_button.click(
        fn=undo_action,
        inputs=[cover_letter_output, history_state, current_index],
        outputs=[cover_letter_output, history_state, current_index]
    )

    redo_button.click(
        fn=redo_action,
        inputs=[cover_letter_output, history_state, current_index],
        outputs=[cover_letter_output, history_state, current_index]
    )

# Launch the Gradio interface.
if __name__ == "__main__":
    demo.launch()
