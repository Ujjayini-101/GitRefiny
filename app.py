"""Flask API server for GitRefiny."""
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from datetime import datetime
import os
from dotenv import load_dotenv

from validators import validate_github_url, ValidationError
from analyzer import RepositoryAnalyzer, AnalyzerError
from generator import READMEGenerator, GeneratorError
from cache import cache_manager

# Load environment variables
load_dotenv()

app = Flask(__name__, static_folder='../frontend', static_url_path='')
CORS(app)

# Initialize components
readme_generator = READMEGenerator()


@app.route('/')
def index():
    """Serve frontend index.html."""
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/api/analyze', methods=['POST'])
def analyze_repository():
    """
    Analyze a GitHub repository.
    
    Request body:
        {
            "repo_url": "https://github.com/owner/repo",
            "token": "optional_pat_token"
        }
    
    Returns:
        Analysis JSON with repo metadata, languages, file tree, etc.
    """
    try:
        data = request.get_json()
        
        if not data or 'repo_url' not in data:
            return jsonify({
                'error': {
                    'code': 'MISSING_FIELD',
                    'message': 'Missing required field: repo_url'
                }
            }), 400
        
        repo_url = data['repo_url']
        # Use token from request, or fall back to environment variable
        token = data.get('token') or os.getenv('GITHUB_TOKEN')
        
        # Validate URL
        try:
            owner, repo = validate_github_url(repo_url)
        except ValidationError as e:
            return jsonify({
                'error': {
                    'code': 'INVALID_URL',
                    'message': str(e)
                }
            }), 400
        
        # Check cache
        cached_result = cache_manager.get_cached_analysis(repo_url)
        if cached_result:
            return jsonify(cached_result.to_dict()), 200
        
        # Analyze repository with token
        analyzer = RepositoryAnalyzer(token=token)
        
        try:
            analysis = analyzer.analyze_repository(owner, repo)
        except AnalyzerError as e:
            error_code = 'ANALYZER_ERROR'
            status_code = 500
            
            if 'not found' in str(e).lower():
                error_code = 'REPO_NOT_FOUND'
                status_code = 404
            elif 'private' in str(e).lower():
                error_code = 'AUTH_REQUIRED'
                status_code = 403
            elif 'invalid' in str(e).lower() or 'expired' in str(e).lower():
                error_code = 'INVALID_TOKEN'
                status_code = 401
            elif 'timeout' in str(e).lower():
                error_code = 'TIMEOUT'
                status_code = 504
            elif 'too large' in str(e).lower():
                error_code = 'REPO_TOO_LARGE'
                status_code = 413
            
            return jsonify({
                'error': {
                    'code': error_code,
                    'message': str(e)
                }
            }), status_code
        
        # Cache result
        cache_manager.cache_analysis(repo_url, analysis)
        
        return jsonify(analysis.to_dict()), 200
    
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': f'Internal server error: {str(e)}'
            }
        }), 500


@app.route('/api/generate', methods=['POST'])
def generate_readme():
    """
    Generate README from analysis.
    
    Request body:
        {
            "repo_url": "https://github.com/owner/repo",
            "sections": ["title", "description", ...],  // optional
            "tone": "professional",  // optional
            "model": "Auto"  // optional
        }
    
    Returns:
        {
            "markdown": "# Generated README...",
            "generated_at": "2025-11-29T10:30:00Z"
        }
    """
    try:
        data = request.get_json()
        
        if not data or 'repo_url' not in data:
            return jsonify({
                'error': {
                    'code': 'MISSING_FIELD',
                    'message': 'Missing required field: repo_url'
                }
            }), 400
        
        repo_url = data['repo_url']
        sections = data.get('sections')
        tone = data.get('tone', 'professional')
        model = data.get('model', 'Auto')
        
        # Get analysis from cache
        analysis = cache_manager.get_cached_analysis(repo_url)
        
        if not analysis:
            return jsonify({
                'error': {
                    'code': 'ANALYSIS_NOT_FOUND',
                    'message': 'Repository analysis not found. Please analyze the repository first.'
                }
            }), 404
        
        # Generate README
        try:
            markdown = readme_generator.generate_readme(
                analysis=analysis,
                sections=sections,
                tone=tone,
                model=model
            )
        except GeneratorError as e:
            return jsonify({
                'error': {
                    'code': 'GENERATION_ERROR',
                    'message': str(e)
                }
            }), 500
        
        return jsonify({
            'markdown': markdown,
            'generated_at': datetime.now().isoformat()
        }), 200
    
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': f'Internal server error: {str(e)}'
            }
        }), 500


@app.route('/api/chat', methods=['POST'])
def chat_assistant():
    """
    Chat assistant endpoint using Groq Llama 3.3 70B.
    Helps users with README-related queries.
    
    Request body:
        {
            "message": "user message",
            "context": "optional context about current README"
        }
    
    Returns:
        {
            "response": "AI assistant response"
        }
    """
    try:
        import requests
        
        data = request.get_json()
        
        if not data or 'message' not in data:
            return jsonify({
                'error': {
                    'code': 'MISSING_FIELD',
                    'message': 'Missing required field: message'
                }
            }), 400
        
        user_message = data.get('message', '').strip()
        context = data.get('context', '')
        
        # Limit message length to prevent token overflow (max 500 chars)
        if len(user_message) > 500:
            user_message = user_message[:500] + '...'
        
        if not user_message:
            return jsonify({
                'error': {
                    'code': 'EMPTY_MESSAGE',
                    'message': 'Message cannot be empty'
                }
            }), 400
        
        # Get Groq API key
        groq_api_key = os.getenv('GROQ_API_KEY', '')
        
        if not groq_api_key:
            return jsonify({
                'error': {
                    'code': 'API_KEY_MISSING',
                    'message': 'Groq API key not configured'
                }
            }), 500
        
        # Build system prompt for README assistant
        system_prompt = """You are a helpful README documentation assistant for GitRefiny, an AI-powered README generator.

Your role:
- Help users improve their README files
- Answer questions about README best practices
- Provide suggestions for README sections
- Explain how to use GitRefiny features
- Give advice on documentation structure

Keep responses:
- Concise (2-3 paragraphs max)
- Practical and actionable
- Focused on README documentation
- Friendly and helpful

If asked about non-README topics, politely redirect to README-related help."""
        
        # Build user message with context
        if context:
            user_prompt = f"Context: {context[:200]}\n\nUser question: {user_message}"
        else:
            user_prompt = user_message
        
        # Call Groq API with Llama 3.3 70B
        url = "https://api.groq.com/openai/v1/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {groq_api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ],
            "max_tokens": 500,  # Limit response length
            "temperature": 0.7
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        if response.status_code != 200:
            error_detail = response.text
            print(f"Groq API error: {error_detail}")
            
            if response.status_code == 429:
                return jsonify({
                    'error': {
                        'code': 'RATE_LIMIT',
                        'message': 'Too many requests. Please wait a moment and try again.'
                    }
                }), 429
            
            return jsonify({
                'error': {
                    'code': 'API_ERROR',
                    'message': 'Failed to get response from AI assistant'
                }
            }), 500
        
        result = response.json()
        
        # Extract response
        if 'choices' in result and len(result['choices']) > 0:
            ai_response = result['choices'][0]['message']['content']
            
            return jsonify({
                'response': ai_response
            }), 200
        else:
            return jsonify({
                'error': {
                    'code': 'NO_RESPONSE',
                    'message': 'No response generated'
                }
            }), 500
            
    except requests.exceptions.Timeout:
        return jsonify({
            'error': {
                'code': 'TIMEOUT',
                'message': 'Request timed out. Please try again.'
            }
        }), 504
    except Exception as e:
        print(f"Chat error: {str(e)}")
        return jsonify({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'An error occurred processing your message'
            }
        }), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    }), 200


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)
