import pymupdf  # The new standard import

def _resize_pdf_to_fixed_size(input_pdf_path, output_pdf_path, width_in=6.5, height_in=8.5):
    """
    Rescales every page of the exported PDF onto a new page of exactly
    width_in x height_in inches, with no margin — the original content
    is scaled to fill the new page completely.
    """
    target_w_pt = width_in * 72
    target_h_pt = height_in * 72

    # Use pymupdf namespace instead of fitz
    src = pymupdf.open(input_pdf_path)
    dst = pymupdf.open()

    for page in src:
        new_page = dst.new_page(width=target_w_pt, height=target_h_pt)
        # Scale the original page's content to fill the new page exactly
        new_page.show_pdf_page(
            pymupdf.Rect(0, 0, target_w_pt, target_h_pt),
            src,
            page.number,
        )

    dst.save(output_pdf_path)
    dst.close()
    src.close()


    