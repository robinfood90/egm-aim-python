import pathlib
from pathlib import Path
import pytest
from src.services.pdf_reader import read_pdf_file

@pytest.fixture
def project_root() -> Path:
    return pathlib.Path(__file__).parent.parent.parent

# 1. Success case: Read a valid PDF file
def test_read_pdf_success(project_root: Path):
    valid_path = project_root / "data/invoices/gulli/CI-255579.pdf"
    
    result = read_pdf_file(file_path=str(valid_path))
    
    assert result.success is True
    assert result.page_count is not None
    assert result.page_count > 0
    assert result.error_message is None

# 2. Failure case: File not found
def test_read_pdf_file_not_found(project_root: Path):
    non_existent_path = project_root / "data/invoices/error-invoices/non_existent_invoice.pdf"
    
    result = read_pdf_file(file_path=str(non_existent_path))
    
    assert result.success is False
    assert result.error_message is not None 
    assert "not found" in result.error_message.lower()

# 3. Failure case: Corrupted PDF file
def test_read_pdf_corrupted(project_root: Path):
    corrupted_path = project_root / "data/invoices/error-invoices/corrupted_pdf_file.pdf"
    
    result = read_pdf_file(file_path=str(corrupted_path))
    
    assert result.success is False
    assert result.error_message is not None

# 4. Failure case: Non-PDF file
def test_read_non_pdf_file(project_root: Path):
    non_pdf_path = project_root / "data/invoices/error-invoices/non_pdf_file.txt"
    
    result = read_pdf_file(file_path=str(non_pdf_path))
    
    assert result.success is False

# 5. Failure case: Path is a directory, not a file
def test_read_pdf_directory_path(project_root: Path):
    dir_path = project_root / "data/invoices/error-invoices/"
    
    result = read_pdf_file(file_path=str(dir_path))
    
    assert result.success is False

# 6. Test to confirm the correct type of Template returned
def test_read_pdf_verify_template_name(project_root: Path):
    gulli_path = project_root / "data/invoices/gulli/CI-255579.pdf"
    mayers_path = project_root / "data/invoices/mayers/TAX INVOICE - 5552306.pdf"
    
    res_gulli = read_pdf_file(file_path=str(gulli_path), is_check_invoice_template=True)
    res_mayers = read_pdf_file(file_path=str(mayers_path), is_check_invoice_template=True)
    
    assert res_gulli.invoice_template == "GULLI"
    assert res_mayers.invoice_template == "MAYERS"