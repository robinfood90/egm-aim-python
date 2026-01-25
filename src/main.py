import pathlib
from src.services.pdf_reader import read_pdf_file
from src.services.extract_product import extract_products_from_text
from src.services.matching import run_matching_process
from src.repositories.invoice import get_oldest_pending_invoice, update_invoice_status
from src.repositories.product_extract import save_extracted_products, save_matching
from src.repositories.category_dictionary import get_all_active_dictionary_rules
from src.repositories.match_candidate import save_match_candidates
from src.constants.enums import InvoiceStatus
from src.utils.display import print_extracted_products, print_matching_results, print_match_candidates

def core_flow():
    """
    Core processing flow:
    1. Get oldest pending invoice from DB
    2. Read PDF file
    3. Extract products from text & save extracted products
    4. Run matching process & save matching results
    """
    
    project_root = pathlib.Path(__file__).parent.parent
    valid_path = project_root / "data/invoices/gulli/CI-265481.pdf"
    
    # 1. Get oldest pending invoice
    invoice = get_oldest_pending_invoice()
    if not invoice:
        print("No pending invoices found")

    else:
        print(f"ID:", invoice.invoice_id)
        print("Processing Invoice:", invoice.invoice_url)

        # 2. Read file
        read_file = read_pdf_file(
            # str(invoice.invoice_url),
            str(valid_path), # Use valid file for testing
            is_extract_all=True,
            is_check_invoice_template=True,
        )
        if read_file.success and read_file.full_text and read_file.invoice_template:
            # 3. Extract products from text & save extracted products
            raw_products = extract_products_from_text(
                full_text=read_file.full_text,
                invoice_template=read_file.invoice_template,
                invoice_id=invoice.invoice_id,
            )
            print(f"✅ Extracted products")
            # print_extracted_products(raw_products)
            if raw_products:
                save_extract_products = save_extracted_products(raw_products)
                if save_extract_products:
                    update_invoice_status(invoice.invoice_id, InvoiceStatus.EXTRACTED)
                    print(f"✅ Extracted products saved")

                    # 4. Matching & update matching products
                    dictionary_rules = get_all_active_dictionary_rules()
                    print(f"Matching ....")
                    matched_results, match_candidates = run_matching_process(save_extract_products, dictionary_rules)
                    # print_matching_results(matched_results)
                    # print_match_candidates(match_candidates)
                    
                    if matched_results:
                        save_matching(matched_results)
                    if match_candidates:
                        save_match_candidates(match_candidates)
                    print(f"✅ Matching results saved")
                    update_invoice_status(invoice.invoice_id, InvoiceStatus.MATCHED)
        else:
            print(f"❌ Read File Failed: {read_file.error_message}")
            update_invoice_status(invoice.invoice_id, InvoiceStatus.FAILED, read_file.error_message)

if __name__ == "__main__":
    core_flow()