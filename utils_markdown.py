import streamlit as st
import streamlit_antd_components as sac

disclaimer_text = """Disclaimer:
The information and recommendations provided by Finley are for educational and informational purposes only and should not be considered as financial advice or a guarantee of future results. Investments in the stock market carry risks, including the potential loss of capital, and past performance does not guarantee future performance.
Before making any investment decisions, you should conduct your own research, evaluate your financial situation, and consider consulting with a licensed financial advisor. Finley does not have access to all market data and cannot account for unforeseen events or changes in market conditions.
By using this service, you acknowledge and accept that all investment decisions are made at your own discretion and risk."""


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


def clear_btn():
    result = sac.buttons(
        [sac.ButtonsItem(label='Clear')],
        index=None,
        size='xs',
        radius='lg',
        color='gray',
        #variant='outlined',
     )

    return result


# Example usage:
#display_md = DisplayMarkdown()

#display_md.display("This is a markdown tab")
#display_md.display("Another markdown tab", color="#FF5733", font_size="18px", tag="p")