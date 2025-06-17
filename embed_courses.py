import os
import json
import openai
import numpy as np
from dotenv import load_dotenv
from tqdm import tqdm
import pickle
from typing import Dict, List, Any

# Load OpenAI API key
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Paths
JSON_DIR = "./CoursesJSON"
EMBEDDINGS_DIR = "./CourseEmbeddings"
os.makedirs(EMBEDDINGS_DIR, exist_ok=True)

def extract_text_for_embedding(course_data: Dict[str, Any]) -> Dict[str, str]:
    """
    Extract relevant text from course JSON for embedding generation
    """
    
    # Extract metadata text
    metadata = course_data.get("_metadata", {})
    course_info = metadata.get("course_info", {})
    instructor = course_info.get("instructor", {})
    
    metadata_text = f"""
    Course: {course_info.get('title', '')} ({course_info.get('code', '')})
    Semester: {course_info.get('semester', '')} {course_info.get('year', '')}
    Credits: {course_info.get('credits', '')}
    Instructor: {instructor.get('name', '')}
    Description: {metadata.get('course_description', '')}
    Learning Outcomes: {' '.join(metadata.get('learning_outcomes', []))}
    Prerequisites: {' '.join(metadata.get('prerequisites', []))}
    """.strip()
    
    # Extract course schedule topics
    schedule = course_data.get("course_schedule", {})
    all_topics = []
    
    for week, content in schedule.items():
        topics = content.get("topics", [])
        if topics:
            all_topics.extend(topics)
    
    topics_text = " ".join(all_topics)
    
    # Extract textbooks
    textbooks = course_data.get("textbooks", [])
    textbook_text = ""
    for book in textbooks:
        if isinstance(book, dict):
            title = book.get("title", "")
            author = book.get("author", "")
            if title or author:
                textbook_text += f"{title} by {author}. "
    
    # Extract assignments
    assignments = course_data.get("assignments", [])
    assignment_text = ""
    for assignment in assignments:
        if isinstance(assignment, dict):
            name = assignment.get("name", "")
            description = assignment.get("description", "")
            assignment_text += f"{name} {description} ".strip() + " "
    
    # Extract grading information
    grading = course_data.get("grading", {})
    breakdown = grading.get("breakdown", {})
    grading_text = ""
    for component, weight in breakdown.items():
        if weight:
            grading_text += f"{component}: {weight} "
    
    # Extract policies
    policies = course_data.get("policies", {})
    policies_text = ""
    for policy_type, policy_content in policies.items():
        if policy_content:
            policies_text += f"{policy_type}: {policy_content} "
    
    return {
        "metadata": metadata_text,
        "topics": topics_text,
        "textbooks": textbook_text.strip(),
        "assignments": assignment_text.strip(),
        "grading": grading_text.strip(),
        "policies": policies_text.strip(),
        "combined": f"{metadata_text} {topics_text} {textbook_text} {assignment_text} {grading_text} {policies_text}".strip()
    }

def generate_embeddings(texts: List[str], batch_size: int = 100) -> List[List[float]]:
    """
    Generate embeddings for a list of texts using OpenAI's text-embedding-3-small model
    """
    embeddings = []
    
    for i in tqdm(range(0, len(texts), batch_size), desc="Generating embeddings"):
        batch = texts[i:i + batch_size]
        
        try:
            response = openai.embeddings.create(
                model="text-embedding-3-small",  # Cost-effective embedding model
                input=batch,
                encoding_format="float"
            )
            
            batch_embeddings = [item.embedding for item in response.data]
            embeddings.extend(batch_embeddings)
            
        except Exception as e:
            print(f"Error generating embeddings for batch {i//batch_size + 1}: {str(e)}")
            # Add zero embeddings for failed batch
            embeddings.extend([[0.0] * 1536] * len(batch))  # text-embedding-3-small has 1536 dimensions
    
    return embeddings

def process_course_files():
    """
    Process all JSON files and generate embeddings
    """
    json_files = [f for f in os.listdir(JSON_DIR) if f.endswith('.json')]
    
    if not json_files:
        print(f"No JSON files found in {JSON_DIR}")
        return
    
    print(f"Found {len(json_files)} JSON files to process")
    
    all_course_data = []
    failed_files = []
    
    # Load all JSON files
    for json_file in tqdm(json_files, desc="Loading JSON files"):
        try:
            file_path = os.path.join(JSON_DIR, json_file)
            with open(file_path, 'r', encoding='utf-8') as f:
                course_data = json.load(f)
            
            # Extract text for embedding
            extracted_texts = extract_text_for_embedding(course_data)
            
            all_course_data.append({
                'filename': json_file,
                'course_code': course_data.get('_metadata', {}).get('course_info', {}).get('code', ''),
                'course_title': course_data.get('_metadata', {}).get('course_info', {}).get('title', ''),
                'semester': course_data.get('_metadata', {}).get('course_info', {}).get('semester', ''),
                'year': course_data.get('_metadata', {}).get('course_info', {}).get('year', ''),
                'extracted_texts': extracted_texts,
                'original_data': course_data
            })
            
        except Exception as e:
            print(f"Error loading {json_file}: {str(e)}")
            failed_files.append(json_file)
    
    if not all_course_data:
        print("No valid course data found")
        return
    
    print(f"Successfully loaded {len(all_course_data)} courses")
    if failed_files:
        print(f"Failed to load {len(failed_files)} files: {failed_files[:5]}")
    
    # Prepare texts for embedding generation
    embedding_categories = ['metadata', 'topics', 'combined']
    
    for category in embedding_categories:
        print(f"\nProcessing {category} embeddings...")
        
        # Extract texts for this category
        texts = []
        valid_indices = []
        
        for i, course in enumerate(all_course_data):
            text = course['extracted_texts'].get(category, '').strip()
            if text:  # Only process non-empty texts
                texts.append(text)
                valid_indices.append(i)
            else:
                print(f"Warning: Empty {category} text for {course['filename']}")
        
        if not texts:
            print(f"No valid texts found for {category}")
            continue
        
        # Generate embeddings
        print(f"Generating embeddings for {len(texts)} {category} texts...")
        embeddings = generate_embeddings(texts)
        
        # Save embeddings with metadata
        embedding_data = {
            'embeddings': embeddings,
            'metadata': []
        }
        
        for i, embedding in enumerate(embeddings):
            course_idx = valid_indices[i]
            course = all_course_data[course_idx]
            
            embedding_data['metadata'].append({
                'filename': course['filename'],
                'course_code': course['course_code'],
                'course_title': course['course_title'],
                'semester': course['semester'],
                'year': course['year'],
                'text': texts[i],
                'embedding_dim': len(embedding)
            })
        
        # Save to file
        output_file = os.path.join(EMBEDDINGS_DIR, f"{category}_embeddings.pkl")
        with open(output_file, 'wb') as f:
            pickle.dump(embedding_data, f)
        
        print(f"Saved {len(embeddings)} {category} embeddings to {output_file}")
        
        # Also save as JSON for easier inspection (without embeddings to keep file size reasonable)
        metadata_file = os.path.join(EMBEDDINGS_DIR, f"{category}_metadata.json")
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(embedding_data['metadata'], f, indent=2)
        
        print(f"Saved {category} metadata to {metadata_file}")
    
    # Save a summary file
    summary = {
        'total_courses': len(all_course_data),
        'failed_files': failed_files,
        'courses_by_semester': {},
        'courses_by_code': {},
        'embedding_info': {
            'model_used': 'text-embedding-3-small',
            'embedding_dimension': 1536,
            'categories': embedding_categories
        }
    }
    
    # Group by semester and course code
    for course in all_course_data:
        semester_key = f"{course['semester']} {course['year']}".strip()
        if semester_key:
            if semester_key not in summary['courses_by_semester']:
                summary['courses_by_semester'][semester_key] = []
            summary['courses_by_semester'][semester_key].append(course['course_code'])
        
        if course['course_code']:
            if course['course_code'] not in summary['courses_by_code']:
                summary['courses_by_code'][course['course_code']] = []
            summary['courses_by_code'][course['course_code']].append(semester_key)
    
    summary_file = os.path.join(EMBEDDINGS_DIR, "embedding_summary.json")
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\nSaved summary to {summary_file}")
    print(f"\nProcessing complete!")
    print(f"Total courses processed: {len(all_course_data)}")
    print(f"Embedding files saved in: {EMBEDDINGS_DIR}")

def load_embeddings(category: str) -> Dict[str, Any]:
    """
    Helper function to load embeddings from pickle file
    """
    embedding_file = os.path.join(EMBEDDINGS_DIR, f"{category}_embeddings.pkl")
    
    if not os.path.exists(embedding_file):
        raise FileNotFoundError(f"Embedding file not found: {embedding_file}")
    
    with open(embedding_file, 'rb') as f:
        return pickle.load(f)

def search_similar_courses(query_text: str, category: str = 'combined', top_k: int = 5) -> List[Dict[str, Any]]:
    """
    Find similar courses based on text query
    """
    # Generate embedding for query
    query_embedding = generate_embeddings([query_text])[0]
    
    # Load course embeddings
    embedding_data = load_embeddings(category)
    course_embeddings = embedding_data['embeddings']
    metadata = embedding_data['metadata']
    
    # Calculate cosine similarities
    query_embedding = np.array(query_embedding)
    similarities = []
    
    for i, course_embedding in enumerate(course_embeddings):
        course_embedding = np.array(course_embedding)
        
        # Cosine similarity
        similarity = np.dot(query_embedding, course_embedding) / (
            np.linalg.norm(query_embedding) * np.linalg.norm(course_embedding)
        )
        
        similarities.append({
            'similarity': similarity,
            'metadata': metadata[i]
        })
    
    # Sort by similarity and return top k
    similarities.sort(key=lambda x: x['similarity'], reverse=True)
    return similarities[:top_k]

if __name__ == "__main__":
    # Check if OpenAI API key is loaded
    if not openai.api_key:
        print("ERROR: OpenAI API key not found! Please check your .env file.")
        exit(1)
    
    print(f"OpenAI API key loaded (ends with: ...{openai.api_key[-4:]})")
    
    # Process all course files and generate embeddings
    process_course_files()
import os
import json
import pickle
import numpy as np
from openai import OpenAI
from dotenv import load_dotenv
from tqdm import tqdm
import time
from typing import Dict, List, Any

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Paths
JSON_DIR = "./CoursesJSON"
EMBEDDINGS_FILE = "./course_embeddings.pkl"

def get_embedding(text: str, model: str = "text-embedding-3-small", max_retries: int = 3) -> List[float]:
    """
    Get embedding for a given text using OpenAI's embedding API
    """
    for attempt in range(max_retries):
        try:
            # Clean and prepare text
            text = text.replace("\n", " ").strip()
            if not text:
                return []
            
            response = client.embeddings.create(
                input=text,
                model=model
            )
            return response.data[0].embedding
            
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"  Embedding API error, retrying... (attempt {attempt + 1}): {str(e)}")
                time.sleep(2)
            else:
                print(f"  Failed to get embedding after {max_retries} attempts: {str(e)}")
                return []
    
    return []

def extract_course_text_for_embedding(course_data: Dict[str, Any]) -> Dict[str, str]:
    """
    Extract relevant text from course data for embedding generation
    """
    metadata = course_data.get("_metadata", {})
    course_info = metadata.get("course_info", {})
    
    # Extract course metadata text
    course_metadata_parts = []
    
    # Basic course info
    if course_info.get("title"):
        course_metadata_parts.append(f"Course: {course_info['title']}")
    if course_info.get("code"):
        course_metadata_parts.append(f"Code: {course_info['code']}")
    if metadata.get("course_description"):
        course_metadata_parts.append(f"Description: {metadata['course_description']}")
    
    # Learning outcomes
    learning_outcomes = metadata.get("learning_outcomes", [])
    if learning_outcomes:
        course_metadata_parts.append(f"Learning Outcomes: {'; '.join(learning_outcomes)}")
    
    # Prerequisites
    prerequisites = metadata.get("prerequisites", [])
    if prerequisites:
        course_metadata_parts.append(f"Prerequisites: {'; '.join(prerequisites)}")
    
    # Textbooks
    textbooks = course_data.get("textbooks", [])
    if textbooks:
        textbook_info = []
        for book in textbooks:
            book_parts = []
            if book.get("title"):
                book_parts.append(book["title"])
            if book.get("author"):
                book_parts.append(f"by {book['author']}")
            if book_parts:
                textbook_info.append(" ".join(book_parts))
        if textbook_info:
            course_metadata_parts.append(f"Textbooks: {'; '.join(textbook_info)}")
    
    course_metadata_text = " | ".join(course_metadata_parts)
    
    # Extract course schedule topics
    schedule_topics = []
    course_schedule = course_data.get("course_schedule", {})
    
    for week_key, week_data in course_schedule.items():
        topics = week_data.get("topics", [])
        if topics:
            # Add week context to topics
            week_topics = [f"{topic} (Week {week_key.replace('week', '')})" for topic in topics]
            schedule_topics.extend(week_topics)
    
    schedule_text = "; ".join(schedule_topics) if schedule_topics else ""
    
    return {
        "metadata": course_metadata_text,
        "schedule_topics": schedule_text,
        "combined": f"{course_metadata_text} | Topics: {schedule_text}" if schedule_text else course_metadata_text
    }

def process_course_embeddings():
    """
    Process all JSON files and create embeddings
    """
    # Check if embeddings file already exists
    if os.path.exists(EMBEDDINGS_FILE):
        print(f"Loading existing embeddings from {EMBEDDINGS_FILE}")
        with open(EMBEDDINGS_FILE, 'rb') as f:
            embeddings_data = pickle.load(f)
        print(f"Loaded embeddings for {len(embeddings_data)} courses")
        return embeddings_data
    
    # Get all JSON files
    json_files = [f for f in os.listdir(JSON_DIR) if f.endswith('.json')]
    print(f"Found {len(json_files)} JSON files to process")
    
    embeddings_data = {}
    
    for json_file in tqdm(json_files, desc="Processing course embeddings"):
        try:
            # Load course data
            with open(os.path.join(JSON_DIR, json_file), 'r', encoding='utf-8') as f:
                course_data = json.load(f)
            
            print(f"Processing: {json_file}")
            
            # Extract text for embedding
            texts = extract_course_text_for_embedding(course_data)
            
            # Generate embeddings
            embeddings = {}
            for text_type, text_content in texts.items():
                if text_content.strip():
                    embedding = get_embedding(text_content)
                    if embedding:
                        embeddings[text_type] = embedding
                        print(f"  Generated {text_type} embedding ({len(embedding)} dimensions)")
                    else:
                        print(f"  Failed to generate {text_type} embedding")
                else:
                    print(f"  Skipping empty {text_type} text")
            
            # Store course information along with embeddings
            course_key = json_file.replace('.json', '')
            embeddings_data[course_key] = {
                'course_info': course_data.get('_metadata', {}).get('course_info', {}),
                'texts': texts,
                'embeddings': embeddings,
                'source_file': json_file
            }
            
        except Exception as e:
            print(f"Error processing {json_file}: {str(e)}")
            continue
    
    # Save embeddings to pickle file
    print(f"\nSaving embeddings to {EMBEDDINGS_FILE}")
    with open(EMBEDDINGS_FILE, 'wb') as f:
        pickle.dump(embeddings_data, f)
    
    print(f"Successfully processed {len(embeddings_data)} courses")
    return embeddings_data

def load_embeddings() -> Dict[str, Any]:
    """
    Load embeddings from pickle file
    """
    if not os.path.exists(EMBEDDINGS_FILE):
        print(f"Embeddings file {EMBEDDINGS_FILE} not found!")
        return {}
    
    with open(EMBEDDINGS_FILE, 'rb') as f:
        embeddings_data = pickle.load(f)
    
    print(f"Loaded embeddings for {len(embeddings_data)} courses")
    return embeddings_data

def cosine_similarity(a: List[float], b: List[float]) -> float:
    """
    Calculate cosine similarity between two vectors
    """
    a = np.array(a)
    b = np.array(b)
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def search_similar_courses(query: str, embeddings_data: Dict[str, Any], 
                          embedding_type: str = "combined", top_k: int = 5) -> List[Dict[str, Any]]:
    """
    Search for courses similar to a query
    
    Args:
        query: Search query text
        embeddings_data: Loaded embeddings data
        embedding_type: Type of embedding to use ("metadata", "schedule_topics", or "combined")
        top_k: Number of top results to return
    """
    # Get query embedding
    query_embedding = get_embedding(query)
    if not query_embedding:
        print("Failed to generate query embedding")
        return []
    
    # Calculate similarities
    similarities = []
    for course_key, course_data in embeddings_data.items():
        if embedding_type in course_data['embeddings']:
            course_embedding = course_data['embeddings'][embedding_type]
            similarity = cosine_similarity(query_embedding, course_embedding)
            
            similarities.append({
                'course_key': course_key,
                'similarity': similarity,
                'course_info': course_data['course_info'],
                'source_file': course_data['source_file']
            })
    
    # Sort by similarity and return top results
    similarities.sort(key=lambda x: x['similarity'], reverse=True)
    return similarities[:top_k]

# Example usage
if __name__ == "__main__":
    # Check if OpenAI API key is available
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  ERROR: OpenAI API key not found! Please set OPENAI_API_KEY in your .env file.")
        exit(1)
    
    # Process embeddings (will load existing if available)
    embeddings_data = process_course_embeddings()
    
    # Example: Search for similar courses
    if embeddings_data:
        print("\n" + "="*50)
        print("EXAMPLE: Searching for machine learning related courses")
        print("="*50)
        
        query = "machine learning algorithms and mathematical foundations"
        results = search_similar_courses(query, embeddings_data, top_k=3)
        
        for i, result in enumerate(results, 1):
            course_info = result['course_info']
            print(f"\n{i}. {course_info.get('title', 'Unknown Title')} ({course_info.get('code', 'Unknown Code')})")
            print(f"   Similarity: {result['similarity']:.4f}")
            print(f"   File: {result['source_file']}")
    # Example usage of similarity search
    print("\n" + "="*50)
    print("EXAMPLE: Finding courses similar to 'machine learning'")
    print("="*50)
    
    try:
        similar_courses = search_similar_courses("machine learning", category='combined', top_k=3)
        
        for i, result in enumerate(similar_courses, 1):
            metadata = result['metadata']
            print(f"\n{i}. {metadata['course_code']} - {metadata['course_title']}")
            print(f"   Semester: {metadata['semester']} {metadata['year']}")
            print(f"   Similarity: {result['similarity']:.4f}")
            print(f"   File: {metadata['filename']}")
    
    except Exception as e:
        print(f"Error in similarity search example: {str(e)}")