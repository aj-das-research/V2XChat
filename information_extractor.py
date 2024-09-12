import os
import re
import sys
import shutil
import tempfile
from datetime import datetime
from urllib.parse import urlparse
 
import requests
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import ContentFormat
import pypdf
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv
 
BORDER_SYMBOL = "|"
 
 
class DocIntOcr:
    """
    Useful Functions
 
    extract_matching_chunks
 
    """
 
    def __init__(self):
        load_dotenv()
        self.endpoint = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT")
        self.key = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_KEY")
        self.azure_account_name = os.getenv("AZURE_ACCOUNT_NAME")
        self.azure_account_key = os.getenv("AZURE_ACCOUNT_KEY")
        self.azure_container_name = os.getenv("AZURE_CONTAINER_NAME")

        #TODO -> change containers based on need functionality
        self.azure_pdf_container_name = os.getenv("AZURE_CONTAINER_NAME")
        self.azure_ocr_container_name = os.getenv("AZURE_CONTAINER_NAME")
        self.client = DocumentIntelligenceClient(
            endpoint=self.endpoint,
            credential=AzureKeyCredential(self.key)
        )
 
    def split_ocr_pagewise(self,ocr_content):
        # Attempt to split using PageFooter
        pages = re.split(r'<!-- PageFooter="[^"]+" -->', ocr_content)
 
        # Check if the last page is an empty string or matches the pattern for PageNumber
        if len(pages[-1].strip()) == 0 or re.match(r'^\s*<!-- PageNumber="\d+" -->\s*$', pages[-1].strip()):
            pages = pages[:-1]
 
        # If the pages split by PageFooter are less than 10, split using PageHeader
        if len(pages) < 10:
            pages = re.split(r'<!-- PageHeader="[^"]+" -->', ocr_content)
            if len(pages[-1].strip()) == 0 or re.match(r'^\s*<!-- PageNumber="\d+" -->\s*$', pages[-1].strip()):
                pages = pages[:-1]
 
        print("Total Pages", len(pages))
        return {i + 1: page.strip() for i, page in enumerate(pages) if page.strip()}
 
    def extract_matching_chunks(self, doc_content, keywords):
        """
        Extract matching chunks from the document content based on provided keywords.
 
        :param doc_content: The full content of the document.
        :param keywords: A list of keywords to search for in the document.
        :return: A list of unique matching chunks.
        """
        return combined_context_v2(doc_content, keywords)
 
  
    def extract_ocr(self, pdf_input=None):
        """
        Extracts OCR from a PDF file or a folder of PDFs, processes the documents, and uploads the OCR results to Azure Blob Storage.

        :param pdf_input: URL of the PDF file to process or a folder path containing PDFs.
        :return: URL of the uploaded OCR file in Azure Blob Storage.
        """
        # Create a temporary directory for file handling
        temp_dir = tempfile.mkdtemp()

        try:
            # If pdf_input is a URL, handle it as before
            if pdf_input.startswith("http"):
                pdf_file_name = os.path.join(temp_dir, os.path.basename(urlparse(pdf_input).path))

                # Download the PDF file
                response = requests.get(pdf_input, stream=True)
                if response.status_code == 200:
                    with open(pdf_file_name, 'wb') as f:
                        response.raw.decode_content = True
                        shutil.copyfileobj(response.raw, f)
                    print(f"PDF downloaded at {pdf_file_name}")

                    # Process the downloaded PDF
                    blob_url = self.process_large_pdf(pdf_file_name, os.path.splitext(pdf_file_name)[0])
                    return blob_url
                else:
                    print(f"Failed to download the file, status code: {response.status_code}")
                    return None

            # If pdf_input is a folder, process each PDF in the folder
            elif os.path.isdir(pdf_input):
                for pdf_file in os.listdir(pdf_input):
                    if pdf_file.endswith(".pdf"):
                        pdf_file_path = os.path.join(pdf_input, pdf_file)
                        print(f"Processing PDF: {pdf_file_path}")
                        blob_url = self.process_large_pdf(pdf_file_path, os.path.splitext(pdf_file_path)[0])
                        print(f"Uploaded OCR result to: {blob_url}")
                return "All files processed and uploaded."

            # If pdf_input is a single file path, process the PDF file
            elif os.path.isfile(pdf_input) and pdf_input.endswith(".pdf"):
                print(f"Processing single PDF file: {pdf_input}")
                blob_url = self.process_large_pdf(pdf_input, os.path.splitext(pdf_input)[0])
                return blob_url

            else:
                print("Invalid input. Provide either a PDF URL, a folder path, or a PDF file path.")
                return None

        finally:
            # Cleanup temporary files
            self.cleanup(temp_dir)



    def log_processing_status(self, file_name, status):
        """
        Logs the processing status of a file in the status.txt file.
        """
        status_file = "status.txt"
        with open(status_file, "a") as log_file:
            log_file.write(f"{datetime.now()} - {file_name}: {status}\n")
 
    def split_pdf(self, input_file, output_prefix, chunk_size=150):
        """Splits a PDF file into smaller chunks."""
        file_names = []
        with open(input_file, "rb") as pdf_file:
            reader = pypdf.PdfReader(pdf_file)
            num_pages = len(reader.pages)
 
            for i in range(0, num_pages, chunk_size):
                start_page = i
                end_page = min(i + chunk_size, num_pages)
 
                writer = pypdf.PdfWriter()
                for page_num in range(start_page, end_page):
                    writer.add_page(reader.pages[page_num])
 
                output_filename = f"{output_prefix}_{start_page + 1}-{end_page}.pdf"
                file_names.append(output_filename)
                with open(output_filename, "wb") as output_file:
                    writer.write(output_file)
        return file_names
 
    def identify_and_merge_cross_page_tables(self, input_file_path, output_file_path):
        """Processes a single PDF chunk to identify and merge cross-page tables."""
        with open(input_file_path, "rb") as f:
            poller = self.client.begin_analyze_document(
                "prebuilt-layout",
                analyze_request=f,
                content_type="application/octet-stream",
                output_content_format=ContentFormat.MARKDOWN,
            )
 
        result = poller.result()
 
        merge_tables_candidates, table_integral_span_list = self.get_merge_table_candidates_and_table_integral_span(
            result.tables)
 
        SEPARATOR_LENGTH_IN_MARKDOWN_FORMAT = 2
        merged_table_list = []
        for i, merged_table in enumerate(merge_tables_candidates):
            pre_table_idx = merged_table["pre_table_idx"]
            start = merged_table["start"]
            end = merged_table["end"]
            has_paragraph = self.check_paragraph_presence(result.paragraphs, start, end)
 
            is_horizontal = self.check_tables_are_horizontal_distribution(result, pre_table_idx)
            is_vertical = (
                    not has_paragraph and
                    result.tables[pre_table_idx].column_count
                    == result.tables[pre_table_idx + 1].column_count
                    and table_integral_span_list[pre_table_idx + 1]["min_offset"]
                    - table_integral_span_list[pre_table_idx]["max_offset"]
                    <= SEPARATOR_LENGTH_IN_MARKDOWN_FORMAT
            )
 
            if is_vertical or is_horizontal:
                remark = ""
                cur_content = result.content[table_integral_span_list[pre_table_idx + 1]["min_offset"]:
                                             table_integral_span_list[pre_table_idx + 1]["max_offset"]]
 
                if is_horizontal:
                    remark = result.content[table_integral_span_list[pre_table_idx]["max_offset"]:
                                            table_integral_span_list[pre_table_idx + 1]["min_offset"]]
 
                merged_list_len = len(merged_table_list)
                if merged_list_len > 0 and len(merged_table_list[-1]["table_idx_list"]) > 0 and \
                        merged_table_list[-1]["table_idx_list"][-1] == pre_table_idx:
                    merged_table_list[-1]["table_idx_list"].append(pre_table_idx + 1)
                    merged_table_list[-1]["offset"]["max_offset"] = table_integral_span_list[pre_table_idx + 1][
                        "max_offset"]
                    if is_vertical:
                        merged_table_list[-1]["content"] = self.merge_vertical_tables(merged_table_list[-1]["content"],
                                                                                      cur_content)
                    elif is_horizontal:
                        merged_table_list[-1]["content"] = self.merge_horizontal_tables(
                            merged_table_list[-1]["content"],
                            cur_content)
                        merged_table_list[-1]["remark"] += remark
 
                else:
                    pre_content = result.content[table_integral_span_list[pre_table_idx]["min_offset"]:
                                                 table_integral_span_list[pre_table_idx]["max_offset"]]
                    merged_table = {
                        "table_idx_list": [pre_table_idx, pre_table_idx + 1],
                        "offset": {
                            "min_offset": table_integral_span_list[pre_table_idx]["min_offset"],
                            "max_offset": table_integral_span_list[pre_table_idx + 1]["max_offset"],
                        },
                        "content": self.merge_vertical_tables(pre_content,
                                                              cur_content) if is_vertical else self.merge_horizontal_tables(
                            pre_content, cur_content),
                        "remark": remark.strip() if is_horizontal else ""
                    }
 
                    if merged_list_len <= 0:
                        merged_table_list = [merged_table]
                    else:
                        merged_table_list.append(merged_table)
 
        optimized_content = ""
        if merged_table_list:
            start_idx = 0
            for merged_table in merged_table_list:
                optimized_content += result.content[start_idx: merged_table["offset"]["min_offset"]] + merged_table[
                    "content"] + merged_table["remark"]
                start_idx = merged_table["offset"]["max_offset"]
 
            optimized_content += result.content[start_idx:]
        else:
            optimized_content = result.content
 
        with open(output_file_path, "w") as file:
            file.write(optimized_content)
 
    def merge_horizontal_tables(self,md_table_1, md_table_2):
        """
        Merge two consecutive horizontal markdown tables into one markdown table.
 
        Args:
            md_table_1: markdown table 1
            md_table_2: markdown table 2
 
        Returns:
            string: merged markdown table
        """
        rows1 = md_table_1.strip().splitlines()
        rows2 = md_table_2.strip().splitlines()
 
        merged_rows = []
        for row1, row2 in zip(rows1, rows2):
            merged_row = (
                    (row1[:-1] if row1.endswith(BORDER_SYMBOL) else row1)
                    + BORDER_SYMBOL
                    + (row2[1:] if row2.startswith(BORDER_SYMBOL) else row2)
            )
            merged_rows.append(merged_row)
 
        merged_table = "\n".join(merged_rows)
        return merged_table
 
    def remove_header_from_markdown_table(self,markdown_table):
        """
        If an actual table is distributed into two pages vertically. From analysis result, it will be generated as two tables in markdown format.
        Before merging them into one table, it need to be removed the markdown table-header format string. This function implement that.
 
        Args:
            markdown_table: the markdown table string which need to be removed the markdown table-header.
        Returns:
            string: the markdown table string without table-header.
        """
        HEADER_SEPARATOR_CELL_CONTENT = " - "
 
        result = ""
        lines = markdown_table.splitlines()
        for line in lines:
            border_list = line.split(HEADER_SEPARATOR_CELL_CONTENT)
            border_set = set(border_list)
            if len(border_set) == 1 and border_set.pop() == BORDER_SYMBOL:
                continue
            else:
                result += f"{line}\n"
 
        return result
 
    def upload_to_azure(self, file_path, file_name):
        """Uploads a file to Azure Blob Storage."""
        file_name_ocr = f"{os.path.splitext(file_name)[0]}_ocr.md"
        blob_service_client = BlobServiceClient(
            account_url=f"https://{self.azure_account_name}.blob.core.windows.net",
            credential=self.azure_account_key
        )
        blob_client = blob_service_client.get_blob_client(container=self.azure_container_name, blob=file_name_ocr)
 
        with open(file_path, "rb") as data:
            blob_client.upload_blob(data, overwrite=True)
 
        blob_url = f"https://{self.azure_account_name}.blob.core.windows.net/{self.azure_container_name}/{file_name_ocr}"
        return blob_url
 
    # def process_large_pdf(self, input_file, output_prefix, chunk_size=150):
    #     """Splits the PDF into chunks, processes each, and merges the markdown output."""
    #     self.log_processing_status(input_file, "started")
    #     chunk_files = self.split_pdf(input_file, output_prefix, chunk_size)
    #     print('chunk_files',chunk_files)
 
    #     markdown_files = []
    #     for chunk_file in chunk_files:
    #         output_file_path = f"{chunk_file[:-4]}.md"
    #         self.identify_and_merge_cross_page_tables(chunk_file, output_file_path)
    #         markdown_files.append(output_file_path)
 
    #     final_output = self.merge_markdown_files(markdown_files)
 
    #     final_output_file = f"{output_prefix}.md"
    #     with open(final_output_file, "w") as file:
    #         file.write(final_output)
 
    #     blob_url = self.upload_to_azure(final_output_file, os.path.basename(final_output_file))
    #     self.log_processing_status(input_file, "completed")
 
    #     return blob_url

    def process_large_pdf(self, input_file, output_prefix, chunk_size=150):
        """Splits the PDF into chunks, processes each, and returns the markdown output."""
        self.log_processing_status(input_file, "started")
        chunk_files = self.split_pdf(input_file, output_prefix, chunk_size)
        print('chunk_files', chunk_files)

        markdown_files = []
        for chunk_file in chunk_files:
            output_file_path = f"{chunk_file[:-4]}.md"
            self.identify_and_merge_cross_page_tables(chunk_file, output_file_path)
            markdown_files.append(output_file_path)

        final_output = self.merge_markdown_files(markdown_files)

        final_output_file = f"{output_prefix}.md"
        with open(final_output_file, "w") as file:
            file.write(final_output)

        return final_output, final_output_file
 
 
 
    def merge_markdown_files(self, file_list):
        """Merges multiple markdown files into one."""
        merged_content = ""
        for file_name in file_list:
            with open(file_name, "r") as file:
                merged_content += file.read() + "\n"
        return merged_content
 
    def get_table_page_numbers(self,table):
        """
        Returns a list of page numbers where the table appears.
 
        Args:
            table: The table object.
 
        Returns:
            A list of page numbers where the table appears.
        """
        return [region.page_number for region in table.bounding_regions]
 
    def get_table_span_offsets(self,table):
        """
        Calculates the minimum and maximum offsets of a table's spans.
 
        Args:
            table (Table): The table object containing spans.
 
        Returns:
            tuple: A tuple containing the minimum and maximum offsets of the table's spans.
                   If the tuple is (-1, -1), it means the table's spans is empty.
        """
        if table.spans:
            min_offset = table.spans[0].offset
            max_offset = table.spans[0].offset + table.spans[0].length
 
            for span in table.spans:
                if span.offset < min_offset:
                    min_offset = span.offset
                if span.offset + span.length > max_offset:
                    max_offset = span.offset + span.length
 
            return min_offset, max_offset
        else:
            return -1, -1
 
    def merge_vertical_tables(self,md_table_1, md_table_2):
        """
        Merge two consecutive vertical markdown tables into one markdown table.
 
        Args:
            md_table_1: markdown table 1
            md_table_2: markdown table 2
 
        Returns:
            string: merged markdown table
        """
        table2_without_header = self.remove_header_from_markdown_table(md_table_2)
        rows1 = md_table_1.strip().splitlines()
        rows2 = table2_without_header.strip().splitlines()
 
        print(rows1)
        print(rows2)
 
        if rows1 == [] or rows2 == []:
            return table2_without_header
 
        num_columns1 = len(rows1[0].split(BORDER_SYMBOL)) - 2
        num_columns2 = len(rows2[0].split(BORDER_SYMBOL)) - 2
 
        if num_columns1 != num_columns2:
            return table2_without_header
            # raise ValueError("Different count of columns")
 
        merged_rows = rows1 + rows2
        merged_table = '\n'.join(merged_rows)
 
        return merged_table
 
    def check_paragraph_presence(self,paragraphs, start, end):
        """
        Checks if there is a paragraph within the specified range that is not a page header, page footer, or page number. If this were the case, the table would not be a merge table candidate.
 
        Args:
            paragraphs (list): List of paragraphs to check.
            start (int): Start offset of the range.
            end (int): End offset of the range.
 
        Returns:
            bool: True if a paragraph is found within the range that meets the conditions, False otherwise.
        """
        for paragraph in paragraphs:
            if(paragraph.spans is None):
                print(paragraph)
                return False
            for span in paragraph.spans:
                if span.offset > start and span.offset < end:
                    if not hasattr(paragraph, 'role'):
                        return True
                    elif hasattr(paragraph, 'role') and paragraph.role not in ["pageHeader", "pageFooter",
                                                                               "pageNumber"]:
                        return True
        return False
 
    def get_merge_table_candidates_and_table_integral_span(self,tables):
        """
        Find the merge table candidates and calculate the integral span of each table based on the given list of tables.
 
        Parameters:
        tables (list): A list of tables.
 
        Returns:
        list: A list of merge table candidates, where each candidate is a dictionary with keys:
              - pre_table_idx: The index of the first candidate table to be merged (the other table to be merged is the next one).
              - start: The start offset of the 2nd candidate table.
              - end: The end offset of the 1st candidate table.
 
        list: A concision list of result.tables. The significance is to store the calculated data to avoid repeated calculations in subsequent reference.
        """
 
        if tables is None:
            tables = []
        table_integral_span_list = []
        merge_tables_candidates = []
        pre_table_idx = -1
        pre_table_page = -1
        pre_max_offset = 0
 
        for table_idx, table in enumerate(tables):
            min_offset, max_offset = self.get_table_span_offsets(table)
            if min_offset > -1 and max_offset > -1:
                table_page = min(self.get_table_page_numbers(table))
                print(f"Table {table_idx} has offset range: {min_offset} - {max_offset} on page {table_page}")
 
                # If there is a table on the next page, it is a candidate for merging with the previous table.
                if table_page == pre_table_page + 1:
                    pre_table = {
                        "pre_table_idx": pre_table_idx,
                        "start": pre_max_offset,
                        "end": min_offset,
                        "min_offset": min_offset,
                        "max_offset": max_offset,
                    }
                    merge_tables_candidates.append(pre_table)
 
                table_integral_span_list.append(
                    {
                        "idx": table_idx,
                        "min_offset": min_offset,
                        "max_offset": max_offset,
                    }
                )
 
                pre_table_idx = table_idx
                pre_table_page = table_page
                pre_max_offset = max_offset
            else:
                print(f"Table {table_idx} is empty")
                table_integral_span_list.append(
                    {"idx": {table_idx}, "min_offset": -1, "max_offset": -1}
                )
 
        return merge_tables_candidates, table_integral_span_list
 
    def check_tables_are_horizontal_distribution(self,result, pre_table_idx):
        """
        Identify two consecutive pages whether is horizontal distribution.
 
        Args:
             result: the analysis result from document intelligence service.
             pre_table_idx: previous table's index
 
        Returns:
             bool: the two table are horizontal distribution or not.
        """
        INDEX_OF_X_LEFT_TOP = 0
        INDEX_OF_X_LEFT_BOTTOM = 6
        INDEX_OF_X_RIGHT_TOP = 2
        INDEX_OF_X_RIGHT_BOTTOM = 4
 
        THRESHOLD_RATE_OF_RIGHT_COVER = 0.99
        THRESHOLD_RATE_OF_LEFT_COVER = 0.01
 
        is_right_covered = False
        is_left_covered = False
 
        if (
                result.tables[pre_table_idx].row_count
                == result.tables[pre_table_idx + 1].row_count
        ):
            for region in result.tables[pre_table_idx].bounding_regions:
                page_width = result.pages[region.page_number - 1].width
                x_right = max(
                    region.polygon[INDEX_OF_X_RIGHT_TOP],
                    region.polygon[INDEX_OF_X_RIGHT_BOTTOM],
                )
                right_cover_rate = x_right / page_width
                if right_cover_rate > THRESHOLD_RATE_OF_RIGHT_COVER:
                    is_right_covered = True
                    break
 
            for region in result.tables[pre_table_idx + 1].bounding_regions:
                page_width = result.pages[region.page_number - 1].width
                x_left = min(
                    region.polygon[INDEX_OF_X_LEFT_TOP],
                    region.polygon[INDEX_OF_X_LEFT_BOTTOM],
                )
                left_cover_rate = x_left / page_width
                if left_cover_rate < THRESHOLD_RATE_OF_LEFT_COVER:
                    is_left_covered = True
                    break
 
        return is_left_covered and is_right_covered
 
    def cleanup(self, temp_dir):
        """Cleans up the temporary directory after processing."""
        try:
            shutil.rmtree(temp_dir)
            print(f"Temporary directory {temp_dir} deleted successfully.")
        except Exception as e:
            print(f"Error during cleanup: {e}")
 
 
def combined_context_v2(doc_content, keywords, pre_words=100, post_words=200):
    pattern = r'(?si)\b(' + '|'.join(map(re.escape, keywords)) + r')\b'
    regex = re.compile(pattern)
    table_chunks = detect_tables_and_split(doc_content)
    final_chunks = []
 
    for chunk in table_chunks:
        if not chunk['is_table']:
            heading_chunks = detect_headings_and_split(chunk['content'])
            final_chunks.extend(heading_chunks)
        else:
            final_chunks.append(chunk)
 
    matches = []
    last_start = None
    last_end = None
    last_context = ""
 
    for chunk in final_chunks:
        if chunk['is_table']:
            if regex.search(chunk['content']):
                if last_start is not None:
                    if last_end >= 0 and len(chunk['content']) > 0:
                        last_context += f"\n\n{chunk['content']}"
                        last_end = last_end + len(chunk['content'])
                else:
                    matches.append(chunk['content'])
        elif chunk['is_heading']:
            continue
        else:
            for match in regex.finditer(chunk['content']):
                start, end = match.span()
                preceding_text = chunk['content'][:start].split()[-pre_words:]
                following_text = chunk['content'][end:].split()[:post_words]
                context = ' '.join(preceding_text + [match.group()] + following_text)
 
                if last_start is None:
                    last_start = start
                    last_end = end
                    last_context = context
                else:
                    if start <= last_end:
                        last_context += ' ' + context
                        last_end = max(last_end, end)
                    else:
                        matches.append(last_context)
                        last_start = start
                        last_end = end
                        last_context = context
 
                next_chunk_idx = final_chunks.index(chunk) + 1
                while next_chunk_idx < len(final_chunks):
                    next_chunk = final_chunks[next_chunk_idx]
                    if next_chunk.get('is_heading', False):
                        break
                    if next_chunk.get('is_table', False):
                        last_context += f"\n\n{next_chunk['content']}"
                        break
                    next_chunk_idx += 1
 
    if last_context:
        matches.append(last_context)
 
    # Remove duplicates by choosing larger chunks
    unique_matches = []
    for i, match in enumerate(matches):
        is_subset = False
        for other_match in matches:
            if match != other_match and match in other_match:
                is_subset = True
                break
        if not is_subset:
            unique_matches.append(match)
 
    return unique_matches
 
def detect_tables_and_split(content, context_lines=2):
    table_pattern = r'(\|.*?\|\n(?:\|.*?\|\n)+)'
    chunks = []
    last_end = 0
 
    for match in re.finditer(table_pattern, content):
        start_context = content.rfind('\n', 0, match.start())
        if start_context != -1:
            prev_line_start = content.rfind('\n', 0, start_context - 1)
            start_context = prev_line_start if prev_line_start != -1 else 0
 
        if start_context > last_end:
            chunks.append({
                "content": content[last_end:start_context].strip(),
                "is_table": False
            })
 
        end_context = match.end()
        footer_end = content.find('\n', end_context)
        if footer_end != -1:
            end_context = content.find('\n', footer_end + 1)
            if end_context == -1:
                end_context = len(content)
 
        chunks.append({
            "content": content[start_context:end_context].strip(),
            "is_table": True
        })
        last_end = end_context
 
    if last_end < len(content):
        chunks.append({
            "content": content[last_end:].strip(),
            "is_table": False
        })
 
    return chunks
def detect_headings_and_split(content):
    heading_pattern = r'(?m)^(#+\s+.+)$'
    headings = list(re.finditer(heading_pattern, content))
    chunks = []
    last_end = 0
 
    for heading in headings:
        if heading.start() > last_end:
            chunks.append({
                "content": content[last_end:heading.start()].strip(),
                "is_table": False,
                "is_heading": False
            })
 
        chunks.append({
            "content": heading.group().strip(),
            "is_table": False,
            "is_heading": True
        })
        last_end = heading.end()
 
    if last_end < len(content):
        chunks.append({
            "content": content[last_end:].strip(),
            "is_table": False,
            "is_heading": False
        })
 
    return chunks


def save_markdown_locally(markdown_content, file_name):
    """Saves the markdown content to a local folder './extracted_data/'."""
    # Ensure the folder exists
    output_folder = './extracted_data'
    os.makedirs(output_folder, exist_ok=True)
    
    # Define the file path
    output_file_path = os.path.join(output_folder, file_name)
    
    # Write the markdown content to the file
    with open(output_file_path, "w") as file:
        file.write(markdown_content)
    
    print(f"Markdown content saved locally at: {output_file_path}")
    return output_file_path


def save_to_knowledge_base(content, file_name):
    """Saves the markdown content to a local folder './knowledge_base/'."""
    output_folder = './knowledge_base'
    os.makedirs(output_folder, exist_ok=True)
    
    output_file_path = os.path.join(output_folder, file_name)
    
    with open(output_file_path, "w", encoding='utf-8') as file:
        file.write(content)
    
    print(f"Markdown content saved locally at: {output_file_path}")
    return output_file_path



# if __name__ == "__main__":
#     pipeline = DocIntOcr()

#     # Example usage for different scenarios
#     print("Select the use case you want to run:")
#     print("1: Provide a PDF URL")
#     print("2: Provide a folder path containing multiple PDFs")
#     print("3: Provide a single PDF file path")

#     choice = input("Enter the option number (1, 2, or 3): ")

#     if choice == "1":
#         doc_url = input("Enter the PDF URL: ")
#         result = pipeline.extract_ocr(pdf_input=doc_url)
#         if result:
#             print(f"OCR result uploaded to: {result}")
#         else:
#             print("OCR processing failed.")

#     elif choice == "2":
#         folder_path = input("Enter the folder path containing PDFs: ")
#         result = pipeline.extract_ocr(pdf_input=folder_path)
#         if result:
#             print(result)
#         else:
#             print("OCR processing failed.")

#     elif choice == "3":
#         pdf_file_path = input("Enter the path of a single PDF file: ")
#         markdown_content, markdown_file_path = pipeline.process_large_pdf(pdf_file_path, os.path.splitext(pdf_file_path)[0])

#         # Ask if the user wants to save locally or upload
#         save_option = input("Do you want to save the markdown locally? (yes/no): ").lower()

#         if save_option == "yes":
#             # Save markdown locally
#             local_file_path = save_markdown_locally(markdown_content, os.path.basename(markdown_file_path))
#             print(f"Markdown content saved at: {local_file_path}")
#         else:
#             # Upload to Azure
#             blob_url = pipeline.upload_to_azure(markdown_file_path, os.path.basename(markdown_file_path))
#             print(f"OCR result uploaded to: {blob_url}")

#     else:
#         print("Invalid option. Please select 1, 2, or 3.")


if __name__ == "__main__":
    pipeline = DocIntOcr()

    print("Select the use case you want to run:")
    print("1: Provide a PDF URL")
    print("2: Provide a folder path containing multiple PDFs")
    print("3: Provide a single PDF file path")

    choice = input("Enter the option number (1, 2, or 3): ")

    if choice == "1":
        doc_url = input("Enter the PDF URL: ")
        markdown_content, markdown_file_path = pipeline.process_large_pdf(doc_url, os.path.splitext(os.path.basename(doc_url))[0])
        save_to_knowledge_base(markdown_content, os.path.basename(markdown_file_path))

    elif choice == "2":
        folder_path = input("Enter the folder path containing PDFs: ")
        for pdf_file in os.listdir(folder_path):
            if pdf_file.endswith('.pdf'):
                pdf_path = os.path.join(folder_path, pdf_file)
                markdown_content, markdown_file_path = pipeline.process_large_pdf(pdf_path, os.path.splitext(pdf_file)[0])
                save_to_knowledge_base(markdown_content, os.path.basename(markdown_file_path))
        print("All PDFs in the folder have been processed and saved to the knowledge base.")

    elif choice == "3":
        pdf_file_path = input("Enter the path of a single PDF file: ")
        markdown_content, markdown_file_path = pipeline.process_large_pdf(pdf_file_path, os.path.splitext(os.path.basename(pdf_file_path))[0])
        save_to_knowledge_base(markdown_content, os.path.basename(markdown_file_path))

    else:
        print("Invalid option. Please select 1, 2, or 3.")

    print("Processing complete. Markdown content saved in the 'knowledge_base' folder.")
