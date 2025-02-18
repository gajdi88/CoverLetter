import subprocess
import os
from pdf2image import convert_from_path
import gradio as gr


def compile_latex_to_pdf(content, tex_filename="cover_letter.tex", pdf_filename="cover_letter.pdf"):
    """
    Compiles LaTeX content into a PDF.
    """
    latex_template = r"""
    \documentclass[12pt]{letter}
    \usepackage[utf8]{inputenc}
    \usepackage{geometry}
    \geometry{margin=1in}
    \begin{document}
    \begin{letter}{Hiring Manager \\ Company Name \\ Company Address}
    \opening{Dear Hiring Manager,}
    %s
    \closing{Warm regards,\\ xxxx}
    \end{letter}
    \end{document}
    """
    # Escape special characters as needed
    tex_content = latex_template % content.replace('&', r'\&')
    with open(tex_filename, "w") as f:
        f.write(tex_content)
    # Compile the LaTeX file; pdflatex should be installed and in your PATH.
    subprocess.run(["pdflatex", "-interaction=nonstopmode", tex_filename], check=True)
    return pdf_filename


def pdf_to_image(pdf_filename, output_image="cover_letter.png"):
    """
    Converts the first page of a PDF to an image using pdf2image.
    """
    pages = convert_from_path(pdf_filename, dpi=200)
    if pages:
        # Save the first page as a PNG image.
        pages[0].save(output_image, "PNG")
        return output_image
    return None


def generate_cover_letter_preview(cover_letter_text):
    """
    Given the cover letter text, compile it via LaTeX and return an image preview.
    """
    try:
        pdf_filename = compile_latex_to_pdf(cover_letter_text)
        image_file = pdf_to_image(pdf_filename)
        return image_file
    except Exception as e:
        print("Error generating preview:", e)
        return None


# Example Gradio interface showing both text and a preview image.
def preview_cover_letter(cover_letter_text):
    # Generate the preview image file from the cover letter text.
    image_file = generate_cover_letter_preview(cover_letter_text)
    return image_file


# Gradio demo: A textbox for cover letter text and an image preview output.
with gr.Blocks() as demo:
    gr.Markdown("# Cover Letter Preview")
    cover_letter_input = gr.Textbox(label="Cover Letter Text", lines=15,
                                    placeholder="Paste your cover letter text here...")
    preview_button = gr.Button("Generate Preview")
    preview_output = gr.Image(label="LaTeX PDF Preview")

    preview_button.click(fn=preview_cover_letter, inputs=cover_letter_input, outputs=preview_output)

if __name__ == "__main__":
    demo.launch()
