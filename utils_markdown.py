import streamlit as st

class DisplayMarkdown:
    def __init__(self, color="#737578", font_size="16px", tag="h2", text_align="justify"):
        self.color = color
        self.font_size = font_size
        self.tag = tag
        self.text_align = text_align

    def display(self, text, color=None, font_size=None, tag=None, text_align=None):
        # Use the provided color, font_size, tag, and text_align if given, otherwise use the defaults
        color = color if color is not None else self.color
        font_size = font_size if font_size is not None else self.font_size
        tag = tag if tag is not None else self.tag
        text_align = text_align if text_align is not None else self.text_align

        markdown_html = f"""
        <{tag} style='color:{color}; font-size: {font_size}; text-align: {text_align};'>{text}</{tag}>
        """
        st.markdown(markdown_html, unsafe_allow_html=True)

display_md = DisplayMarkdown()

# Example usage:
#display_md = DisplayMarkdown()

#display_md.display("This is a markdown tab")
#display_md.display("Another markdown tab", color="#FF5733", font_size="18px", tag="p")