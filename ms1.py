import os
import json
import time
from datetime import datetime
from pathlib import Path
import PyPDF2
import fitz  # PyMuPDF
from openai import OpenAI
from dotenv import load_dotenv
from typing import Dict, List, Any

# Load environment variables
load_dotenv()

class CourseExtractorWithEmbeddings:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        # Model configurations
        self.extraction_model = 'o3-mini'  # Changed to o3-mini
        self.embedding_model = 'text-embedding-3-small'
        
        # Pricing (per 1K tokens) - Update these with actual o3-mini pricing when available
        self.model_costs = {
            'o3-mini': {
                'input_cost': 0.003,   # Placeholder - update with actual pricing
                'output_cost': 0.012,  # Placeholder - update with actual pricing
            },
            'text-embedding-3-small': {
                'cost': 0.00002,  # $0.02 per 1M tokens
            }
        }
        
        self.extraction_prompt = """
You are an expert at extracting structured information from academic course syllabi. 
Extract ONLY the course schedule and metadata from the provided syllabus text.

Return a JSON object with this EXACT structure:

{
  "course_schedule": {
    "week1": {
      "topics": ["Topic 1", "Topic 2"],
      "readings": ["Reading 1", "Reading 2"],
      "assignments": ["Assignment 1"],
      "due_dates": ["Date 1"]
    },
    "week2": {
      "topics": ["Topic 1"],
      "readings": ["Reading 1"],
      "assignments": ["Assignment 1", "Quiz 1"],
      "due_dates": ["Date 1", "Date 2"]
    }
    // ... continue for all weeks
  },
  "_metadata": {
    "extraction_date": "2025-06-24T10:00:00.000000",
    "source_type": "file",
    "model_used": "o3-mini",
    "course_info": {
      "title": "Course Title",
      "code": "Course Code",
      "credits": "Number",
      "semester": "Season Year",
      "instructor": {
        "name": "Instructor Name",
        "email": "email@domain.com",
        "office_hours": "Office hours info"
      }
    },
    "course_description": "Full course description",
    "learning_outcomes": ["Outcome 1", "Outcome 2"],
    "prerequisites": ["Prereq 1", "Prereq 2"],
    "textbooks": ["Textbook 1", "Textbook 2"]
  }
}

IMPORTANT RULES:
1. Extract ALL weeks/modules/sessions mentioned in the schedule
2. If no specific week numbers, create sequential weeks (week1, week2, etc.)
3. Include ALL topics, readings, assignments, and due dates for each period
4. Fill ALL metadata fields with available information
5. If information is not available, use empty string "" or empty array []
6. Do not include any text outside the JSON object
7. Ensure valid JSON format

Syllabus Text:
"""

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF using both PyPDF2 and PyMuPDF for better coverage"""
        text = ""
        
        # Try PyMuPDF first (better for complex layouts)
        try:
            doc = fitz.open(pdf_path)
            for page in doc:
                text += page.get_text()
            doc.close()
            if text.strip():
                return text
        except Exception as e:
            print(f"PyMuPDF extraction failed: {e}")
        
        # Fallback to PyPDF2
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text()
        except Exception as e:
            print(f"PyPDF2 extraction failed: {e}")
            
        return text

    def extract_course_data(self, text: str, pdf_name: str) -> Dict[str, Any]:
        """Extract course schedule using o3-mini model"""
        
        full_prompt = self.extraction_prompt + text
        start_time = time.time()
        
        try:
            response = self.client.chat.completions.create(
                model=self.extraction_model,
                messages=[
                    {"role": "user", "content": full_prompt}
                ]
            )
            
            end_time = time.time()
            
            # Get response and token counts
            response_text = response.choices[0].message.content
            output_tokens = response.usage.completion_tokens
            input_tokens = response.usage.prompt_tokens
            
            # Calculate costs
            input_cost = (input_tokens / 1000) * self.model_costs[self.extraction_model]['input_cost']
            output_cost = (output_tokens / 1000) * self.model_costs[self.extraction_model]['output_cost']
            total_cost = input_cost + output_cost
            
            # Parse JSON
            try:
                # Clean response text (remove any markdown formatting)
                clean_text = response_text.strip()
                if clean_text.startswith('```json'):
                    clean_text = clean_text[7:]
                if clean_text.endswith('```'):
                    clean_text = clean_text[:-3]
                clean_text = clean_text.strip()
                
                extracted_data = json.loads(clean_text)
                
                # Add metadata
                if '_metadata' not in extracted_data:
                    extracted_data['_metadata'] = {}
                
                extracted_data['_metadata'].update({
                    'extraction_date': datetime.now().isoformat(),
                    'pdf_source': pdf_name,
                    'source_type': 'file',
                    'model_used': self.extraction_model,
                    'text_length': len(text),
                    'processing_time': end_time - start_time,
                    'extraction_cost': total_cost
                })
                
                return {
                    'success': True,
                    'data': extracted_data,
                    'metrics': {
                        'input_tokens': input_tokens,
                        'output_tokens': output_tokens,
                        'cost': total_cost,
                        'processing_time': end_time - start_time
                    }
                }
                
            except json.JSONDecodeError as e:
                print(f"JSON parsing error: {e}")
                return {
                    'success': False,
                    'error': f"JSON parsing failed: {e}",
                    'raw_response': response_text[:500] + "..." if len(response_text) > 500 else response_text
                }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'processing_time': time.time() - start_time
            }

    def create_embeddings_for_course(self, course_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create embeddings module/week-wise or course-wise based on availability"""
        
        # Extract core course information
        course_info = course_data.get('_metadata', {}).get('course_info', {})
        course_name = course_info.get('title', '')
        course_code = course_info.get('code', '')
        course_description = course_data.get('_metadata', {}).get('course_description', '')
        learning_outcomes = course_data.get('_metadata', {}).get('learning_outcomes', [])
        
        # Base course context for all embeddings
        base_context = f"""
        Course Name: {course_name}
        Course Code: {course_code}
        Course Description: {course_description}
        Learning Outcomes: {'; '.join(learning_outcomes)}
        """.strip()
        
        embeddings_list = []
        total_tokens = 0
        
        try:
            schedule = course_data.get('course_schedule', {})
            
            if schedule and len(schedule) > 0:
                # MODULE/WEEK-WISE EMBEDDINGS
                print(f"    Creating {len(schedule)} module/week embeddings...")
                
                for module_key, module_content in schedule.items():
                    topics = module_content.get('topics', [])
                    
                    if topics and any(topic.strip() for topic in topics):
                        # Format module name (week1 -> Week 1, module3 -> Module 3)
                        module_display = module_key.replace('week', 'Week ').replace('module', 'Module ').replace('_', ' ').title()
                        if module_display == module_key:  # If no replacement happened
                            module_display = module_key.replace('_', ' ').title()
                        
                        # Create embedding text with module name AND topic names
                        embedding_text = f"""
                        {base_context}
                        
                        {module_display}
                        Topics: {'; '.join(topics)}
                        """.strip()
                        
                        try:
                            response = self.client.embeddings.create(
                                model=self.embedding_model,
                                input=embedding_text
                            )
                            
                            embedding_entry = {
                                'id': f"{course_code}_{module_key}" if course_code else f"course_{module_key}",
                                'course_name': course_name,
                                'course_code': course_code,
                                'course_description': course_description,
                                'learning_outcomes': learning_outcomes,
                                'module_name': module_key,
                                'module_display_name': module_display,
                                'topics': topics,
                                'embedding_type': 'module',
                                'embedding_text': embedding_text,
                                'vector': response.data[0].embedding,
                                'tokens': response.usage.total_tokens,
                                'created_at': datetime.now().isoformat(),
                                'model_used': self.embedding_model
                            }
                            
                            embeddings_list.append(embedding_entry)
                            total_tokens += response.usage.total_tokens
                            
                        except Exception as e:
                            print(f"      Error creating embedding for {module_key}: {e}")
                            continue
            
            else:
                # COURSE-WISE EMBEDDING (when no modules/weeks available)
                print("    Creating course-level embedding (no modules found)...")
                
                # Create comprehensive course embedding
                embedding_text = f"""
                {base_context}
                
                Full Course Content: This course covers the topics and outcomes described above.
                """.strip()
                
                try:
                    response = self.client.embeddings.create(
                        model=self.embedding_model,
                        input=embedding_text
                    )
                    
                    embedding_entry = {
                        'id': f"{course_code}_full" if course_code else "course_full",
                        'course_name': course_name,
                        'course_code': course_code,
                        'course_description': course_description,
                        'learning_outcomes': learning_outcomes,
                        'module_name': 'full_course',
                        'topics': [],
                        'embedding_type': 'course',
                        'embedding_text': embedding_text,
                        'vector': response.data[0].embedding,
                        'tokens': response.usage.total_tokens,
                        'created_at': datetime.now().isoformat(),
                        'model_used': self.embedding_model
                    }
                    
                    embeddings_list.append(embedding_entry)
                    total_tokens += response.usage.total_tokens
                    
                except Exception as e:
                    print(f"      Error creating course embedding: {e}")
            
            # Calculate embedding costs
            embedding_cost = (total_tokens / 1000) * self.model_costs[self.embedding_model]['cost']
            
            return {
                'success': True,
                'embeddings': embeddings_list,
                'cost': embedding_cost,
                'tokens': total_tokens,
                'course_info': {
                    'name': course_name,
                    'code': course_code,
                    'source': course_data.get('_metadata', {}).get('pdf_source', 'unknown')
                }
            }        
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'embeddings': embeddings_list
            }
    
    def process_pdfs(self, input_dir: str, output_dir: str) -> Dict[str, Any]:
        """Process all PDFs in the input directory and create embeddings"""
        input_path = Path(input_dir)
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Create subdirectories
        json_dir = output_path / "json_extractions"
        json_dir.mkdir(exist_ok=True)
        
        pdf_files = list(input_path.glob("*.pdf"))
        
        if not pdf_files:
            print(f"No PDF files found in {input_dir}")
            return {}
        
        print(f"Found {len(pdf_files)} PDF files")
        
        all_results = {}
        all_embeddings = []  # Single list for all embeddings
        total_extraction_cost = 0
        total_embedding_cost = 0
        processing_summary = {
            'processed_files': 0,
            'successful_extractions': 0,
            'successful_embeddings': 0,
            'total_embeddings_created': 0,
            'files_processed': []
        }
        
        for pdf_file in pdf_files:
            print(f"\nProcessing: {pdf_file.name}")
            file_summary = {
                'filename': pdf_file.name,
                'extraction_success': False,
                'embedding_success': False,
                'embeddings_created': 0,
                'extraction_cost': 0,
                'embedding_cost': 0
            }
            
            # Extract text from PDF
            text = self.extract_text_from_pdf(str(pdf_file))
            if not text.strip():
                print(f"No text extracted from {pdf_file.name}")
                file_summary['error'] = 'No text extracted'
                processing_summary['files_processed'].append(file_summary)
                continue
            
            print(f"Extracted {len(text)} characters")
            
            # Extract course data using o3-mini
            print("  Extracting course data with o3-mini...")
            extraction_result = self.extract_course_data(text, pdf_file.name)
            
            if not extraction_result['success']:
                print(f"  Failed to extract data: {extraction_result.get('error', 'Unknown error')}")
                file_summary['error'] = extraction_result.get('error', 'Unknown error')
                processing_summary['files_processed'].append(file_summary)
                continue
            
            course_data = extraction_result['data']
            extraction_cost = extraction_result['metrics']['cost']
            total_extraction_cost += extraction_cost
            file_summary['extraction_success'] = True
            file_summary['extraction_cost'] = extraction_cost
            processing_summary['successful_extractions'] += 1
            
            # Save JSON extraction
            json_file = json_dir / f"{pdf_file.stem}_extracted.json"
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(course_data, f, indent=2, ensure_ascii=False)
            
            print(f"  Extraction cost: ${extraction_cost:.6f}")
            
            # Create embeddings
            print("  Creating embeddings...")
            embedding_result = self.create_embeddings_for_course(course_data)
            
            if embedding_result['success']:
                embedding_cost = embedding_result['cost']
                total_embedding_cost += embedding_cost
                embeddings_created = len(embedding_result['embeddings'])
                
                # Add embeddings to master list
                all_embeddings.extend(embedding_result['embeddings'])
                
                file_summary['embedding_success'] = True
                file_summary['embedding_cost'] = embedding_cost
                file_summary['embeddings_created'] = embeddings_created
                processing_summary['successful_embeddings'] += 1
                processing_summary['total_embeddings_created'] += embeddings_created
                
                print(f"  Embedding cost: ${embedding_cost:.6f}")
                print(f"  Created {embeddings_created} embeddings")
            else:
                print(f"  Failed to create embeddings: {embedding_result.get('error', 'Unknown error')}")
                file_summary['embedding_error'] = embedding_result.get('error', 'Unknown error')
            
            processing_summary['processed_files'] += 1
            processing_summary['files_processed'].append(file_summary)
            
            all_results[pdf_file.name] = {
                'extraction': extraction_result,
                'embeddings': embedding_result if embedding_result['success'] else None
            }
        
        # Save single JSON file with all embeddings
        if all_embeddings:
            embeddings_json = {
                'embeddings': all_embeddings,
                'metadata': {
                    'total_embeddings': len(all_embeddings),
                    'embedding_model': self.embedding_model,
                    'extraction_model': self.extraction_model,
                    'total_embedding_cost': total_embedding_cost,
                    'total_extraction_cost': total_extraction_cost,
                    'total_cost': total_extraction_cost + total_embedding_cost,
                    'created_at': datetime.now().isoformat(),
                    'processing_summary': processing_summary
                }
            }
            
            embeddings_file = output_path / "all_course_embeddings.json"
            with open(embeddings_file, 'w', encoding='utf-8') as f:
                json.dump(embeddings_json, f, indent=2, ensure_ascii=False)
            
            print(f"\nSaved all embeddings to: {embeddings_file}")
            print(f"Total embeddings in file: {len(all_embeddings)}")
        
        # Create summary report
        summary = {
            'processed_files': processing_summary['processed_files'],
            'successful_extractions': processing_summary['successful_extractions'],
            'successful_embeddings': processing_summary['successful_embeddings'],
            'total_embeddings_created': processing_summary['total_embeddings_created'],
            'total_extraction_cost': total_extraction_cost,
            'total_embedding_cost': total_embedding_cost,
            'total_cost': total_extraction_cost + total_embedding_cost,
            'extraction_model': self.extraction_model,
            'embedding_model': self.embedding_model,
            'processing_date': datetime.now().isoformat(),
            'files_processed': processing_summary['files_processed']
        }
        
        summary_file = output_path / "processing_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        print(f"\n=== PROCESSING COMPLETE ===")
        print(f"Processed: {summary['processed_files']} files")
        print(f"Successful extractions: {summary['successful_extractions']}")
        print(f"Successful embeddings: {summary['successful_embeddings']}")
        print(f"Total embeddings created: {summary['total_embeddings_created']}")
        print(f"Total extraction cost: ${total_extraction_cost:.6f}")
        print(f"Total embedding cost: ${total_embedding_cost:.6f}")
        print(f"Total cost: ${summary['total_cost']:.6f}")
        print(f"\nFiles saved to:")
        print(f"  JSON extractions: {json_dir}")
        print(f"  All embeddings: {output_path}/all_course_embeddings.json")
        print(f"  Summary: {summary_file}")
        
        return {
            'results': all_results,
            'embeddings': all_embeddings,
            'summary': summary
        }

def main():
    """Main execution function"""
    extractor = CourseExtractorWithEmbeddings()
    
    # Configuration
    input_directory = "./StevensCourses"  # Directory containing PDF files
    output_directory = "./course_data"  # Directory to save results
    
    # Ensure input directory exists
    if not os.path.exists(input_directory):
        print(f"Input directory '{input_directory}' not found!")
        print("Please create the directory and add your PDF files.")
        return
    
    # Process all PDFs
    results = extractor.process_pdfs(input_directory, output_directory)
    
    if results:
        print(f"\n=== PROCESSING SUMMARY ===")
        summary = results['summary']
        print(f"Model used: {summary['extraction_model']}")
        print(f"Embedding model: {summary['embedding_model']}")
        print(f"Successfully processed {summary['successful_extractions']} out of {summary['processed_files']} files")
        print(f"Created {summary['total_embeddings_created']} embeddings")

if __name__ == "__main__":
    main()