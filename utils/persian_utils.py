def reshape_persian_text(text):
    if text is None:
        return ""
    
    try:
        import arabic_reshaper
        return arabic_reshaper.reshape(str(text))
    except ImportError:
        # Fallback without reshaping
        return str(text)

def get_bidi_text(text):
    """Get bidirectional text with fallback"""
    try:
        from bidi.algorithm import get_display
        return get_display(text)
    except ImportError:
        # Fallback: simple Persian number conversion
        text = str(text)
        persian_numbers = '۰١٢٣٤٥٦٧٨٩'
        english_numbers = '0123456789'
        for en, fa in zip(english_numbers, persian_numbers):
            text = text.replace(en, fa)
        return text