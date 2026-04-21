# travel_app/huggingface_ai.py
import os
import json
import requests
from dotenv import load_dotenv
import random
from datetime import datetime

load_dotenv()


class HybridHuggingFaceAI:
    """Hybrid AI that uses real Hugging Face models with fallback to simulated AI"""

    def __init__(self):
        self.use_real_ai = False
        self.api_key = os.environ.get('HUGGINGFACE_API_KEY', '')
        self.models_loaded = False
        self.sentiment_pipeline = None
        self.generator_pipeline = None

        # Comprehensive city database with detailed information
        self.city_database = self._initialize_city_database()

        # Try to load real models
        self._initialize_ai()

    def _initialize_city_database(self):
        """Initialize comprehensive city database with detailed information"""
        return {
            'dubai': {
                'name': 'Dubai',
                'country': 'UAE',
                'weather': 'Sunny, 32°C ☀️',
                'weather_detail': 'Hot and sunny year-round. Perfect for outdoor activities in winter months.',
                'best_time': 'November to March',
                'attractions': ['Burj Khalifa', 'Palm Jumeirah', 'Dubai Mall', 'Desert Safari'],
                'cuisine': ['Arabic mezze', 'Shawarma', 'Camel milk chocolate'],
                'budget': 'luxury',
                'price_per_day': 250,
                'category': 'city',
                'activities': ['Desert safari', 'Shopping', 'Fine dining', 'Skydiving']
            },
            'tokyo': {
                'name': 'Tokyo',
                'country': 'Japan',
                'weather': 'Mild, 18°C 🌸',
                'weather_detail': 'Spring brings cherry blossoms. Summers are warm and humid.',
                'best_time': 'March-May or September-November',
                'attractions': ['Shibuya Crossing', 'Senso-ji Temple', 'Tokyo Tower', 'Akihabara'],
                'cuisine': ['Sushi', 'Ramen', 'Tempura', 'Matcha desserts'],
                'budget': 'moderate',
                'price_per_day': 180,
                'category': 'city',
                'activities': ['Temple visits', 'Sushi making', 'Anime shopping', 'Robot restaurant']
            },
            'london': {
                'name': 'London',
                'country': 'UK',
                'weather': 'Cloudy, 16°C ☁️',
                'weather_detail': 'Mild and often cloudy. Pack an umbrella for occasional rain.',
                'best_time': 'May-September',
                'attractions': ['Big Ben', 'London Eye', 'Buckingham Palace', 'British Museum'],
                'cuisine': ['Fish and chips', 'Afternoon tea', 'Sunday roast'],
                'budget': 'moderate',
                'price_per_day': 200,
                'category': 'city',
                'activities': ['Museum visits', 'Theatre shows', 'River Thames cruise', 'Royal parks']
            },
            'new york': {
                'name': 'New York',
                'country': 'USA',
                'weather': 'Moderate, 22°C 🗽',
                'weather_detail': 'Four distinct seasons. Spring and fall are most pleasant.',
                'best_time': 'April-June or September-November',
                'attractions': ['Statue of Liberty', 'Times Square', 'Central Park', 'Empire State Building'],
                'cuisine': ['NY Pizza', 'Bagels', 'Hot dogs', 'Michelin-starred restaurants'],
                'budget': 'luxury',
                'price_per_day': 280,
                'category': 'city',
                'activities': ['Broadway shows', 'Museum tours', 'Shopping', 'Helicopter tour']
            },
            'paris': {
                'name': 'Paris',
                'country': 'France',
                'weather': 'Mild, 18°C 🌹',
                'weather_detail': 'Mild climate. Spring and fall are most beautiful.',
                'best_time': 'April-October',
                'attractions': ['Eiffel Tower', 'Louvre Museum', 'Notre-Dame', 'Champs-Élysées'],
                'cuisine': ['Croissants', 'French pastries', 'Cheese', 'Wine'],
                'budget': 'moderate',
                'price_per_day': 220,
                'category': 'city',
                'activities': ['Art museum visits', 'Seine river cruise', 'Cooking classes', 'Fashion shopping']
            },
            'bali': {
                'name': 'Bali',
                'country': 'Indonesia',
                'weather': 'Warm, 28°C ☀️',
                'weather_detail': 'Tropical climate. Dry season May-September is best.',
                'best_time': 'April-October',
                'attractions': ['Uluwatu Temple', 'Rice Terraces', 'Seminyak Beach', 'Mount Batur'],
                'cuisine': ['Nasi goreng', 'Satay', 'Babi guling'],
                'budget': 'budget',
                'price_per_day': 85,
                'category': 'beach',
                'activities': ['Surfing', 'Yoga', 'Temple visits', 'Spa treatments']
            },
            'swiss alps': {
                'name': 'Swiss Alps',
                'country': 'Switzerland',
                'weather': 'Cool, 12°C ⛅',
                'weather_detail': 'Mountain climate. Summer for hiking, winter for skiing.',
                'best_time': 'December-March (ski) or June-September (hike)',
                'attractions': ['Jungfraujoch', 'Matterhorn', 'Lake Geneva', 'Interlaken'],
                'cuisine': ['Fondue', 'Raclette', 'Swiss chocolate'],
                'budget': 'luxury',
                'price_per_day': 300,
                'category': 'mountain',
                'activities': ['Skiing', 'Hiking', 'Paragliding', 'Scenic train rides']
            },
            'bangkok': {
                'name': 'Bangkok',
                'country': 'Thailand',
                'weather': 'Hot, 32°C 🍜',
                'weather_detail': 'Tropical, hot and humid year-round. Best visited November-February.',
                'best_time': 'November-February',
                'attractions': ['Grand Palace', 'Wat Arun', 'Chatuchak Market', 'Khao San Road'],
                'cuisine': ['Pad Thai', 'Tom Yum Goong', 'Mango sticky rice'],
                'budget': 'budget',
                'price_per_day': 65,
                'category': 'city',
                'activities': ['Temple tours', 'Street food tasting', 'Boat tours', 'Muay Thai']
            },
            'rome': {
                'name': 'Rome',
                'country': 'Italy',
                'weather': 'Pleasant, 24°C 🏛️',
                'weather_detail': 'Mediterranean climate. Spring and fall are ideal.',
                'best_time': 'April-June or September-October',
                'attractions': ['Colosseum', 'Vatican City', 'Trevi Fountain', 'Roman Forum'],
                'cuisine': ['Pasta', 'Pizza', 'Gelato', 'Espresso'],
                'budget': 'moderate',
                'price_per_day': 190,
                'category': 'historical',
                'activities': ['Ancient ruins tours', 'Vatican museums', 'Cooking classes', 'Wine tasting']
            },
            'maldives': {
                'name': 'Maldives',
                'country': 'Maldives',
                'weather': 'Sunny, 28°C 🏝️',
                'weather_detail': 'Tropical paradise. Best from November to April.',
                'best_time': 'November-April',
                'attractions': ['Overwater bungalows', 'Beaches', 'Snorkeling spots', 'Local islands'],
                'cuisine': ['Seafood', 'Coconut-based dishes', 'Fresh tropical fruits'],
                'budget': 'luxury',
                'price_per_day': 450,
                'category': 'beach',
                'activities': ['Snorkeling', 'Diving', 'Sunset cruises', 'Spa treatments']
            },
            'istanbul': {
                'name': 'Istanbul',
                'country': 'Turkey',
                'weather': 'Mild, 20°C 🕌',
                'weather_detail': 'Mediterranean climate. Spring and fall are best.',
                'best_time': 'April-May or September-October',
                'attractions': ['Hagia Sophia', 'Blue Mosque', 'Grand Bazaar', 'Bosphorus Cruise'],
                'cuisine': ['Kebabs', 'Baklava', 'Turkish tea', 'Meze'],
                'budget': 'budget',
                'price_per_day': 95,
                'category': 'historical',
                'activities': ['Mosque visits', 'Bazaar shopping', 'Bosphorus tour', 'Turkish bath']
            },
            'sydney': {
                'name': 'Sydney',
                'country': 'Australia',
                'weather': 'Warm, 24°C 🏖️',
                'weather_detail': 'Subtropical climate. Best in spring and fall.',
                'best_time': 'September-November or March-May',
                'attractions': ['Sydney Opera House', 'Harbour Bridge', 'Bondi Beach', 'Taronga Zoo'],
                'cuisine': ['Seafood', 'Aussie BBQ', 'Meat pies', 'Flat white coffee'],
                'budget': 'moderate',
                'price_per_day': 210,
                'category': 'city',
                'activities': ['Beach surfing', 'Bridge climb', 'Ferry rides', 'Wildlife encounters']
            }
        }

    def _initialize_ai(self):
        """Initialize real Hugging Face models if available"""
        try:
            # Try to load using Hugging Face API
            if self.api_key:
                self.use_real_ai = True
                print("✅ Using Hugging Face Inference API")
                return

            # Try to load local models
            from transformers import pipeline

            print("🔄 Loading Hugging Face models (this may take a few minutes)...")

            # Load sentiment analysis model (small, fast)
            self.sentiment_pipeline = pipeline(
                "sentiment-analysis",
                model="distilbert-base-uncased-finetuned-sst-2-english"
            )

            # Load text generation model
            self.generator_pipeline = pipeline(
                "text-generation",
                model="gpt2",
                max_length=150,
                temperature=0.7,
                pad_token_id=50256
            )

            self.models_loaded = True
            self.use_real_ai = True
            print("✅ Hugging Face models loaded successfully!")

        except Exception as e:
            print(f"⚠️ Could not load Hugging Face models: {e}")
            print("📝 Using simulated AI fallback")
            self.use_real_ai = False
            self.models_loaded = False

    # ==================== CORRECTED API CALL METHOD ====================
    def _call_huggingface_api(self, model, inputs):
        """Call Hugging Face Inference API with correct endpoint"""
        if not self.api_key:
            return None

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # Use the official Hugging Face Inference API endpoint
        # To this (adding /v1/ version)
        api_url = f"https://api-inference.huggingface.co/v1/models/{model}"

        try:
            print(f"📡 Calling Hugging Face API: {model}")
            response = requests.post(api_url, headers=headers, json={"inputs": inputs}, timeout=30)

            if response.status_code == 200:
                print(f"✅ Hugging Face API success!")
                return response.json()
            elif response.status_code == 503:
                print(f"⏳ Model is loading, please try again")
                return None
            else:
                print(f"⚠️ API Error {response.status_code}: {response.text[:200]}")
                return None

        except requests.exceptions.Timeout:
            print(f"⏰ API request timed out")
            return None
        except Exception as e:
            print(f"❌ API Exception: {e}")
            return None

    # ==================== WEATHER & CITY INFO ====================

    def get_city_weather(self, city_name):
        """Get detailed weather information for a city"""
        city_key = city_name.lower()

        if city_key in self.city_database:
            city = self.city_database[city_key]
            return {
                'success': True,
                'city': city['name'],
                'country': city['country'],
                'weather': city['weather'],
                'weather_detail': city['weather_detail'],
                'best_time': city['best_time'],
                'advice': self._get_weather_advice(city['weather'])
            }
        else:
            # Try partial match
            for key, city in self.city_database.items():
                if key in city_name.lower() or city_name.lower() in key:
                    return {
                        'success': True,
                        'city': city['name'],
                        'country': city['country'],
                        'weather': city['weather'],
                        'weather_detail': city['weather_detail'],
                        'best_time': city['best_time'],
                        'advice': self._get_weather_advice(city['weather'])
                    }
            return {'success': False, 'error': f"City '{city_name}' not found in our database"}

    def get_all_weather(self):
        """Get weather for all major cities"""
        weather_list = []
        for key, city in self.city_database.items():
            weather_list.append({
                'city': city['name'],
                'country': city['country'],
                'weather': city['weather'],
                'temperature': self._extract_temperature(city['weather'])
            })
        return weather_list

    def _extract_temperature(self, weather_string):
        """Extract temperature from weather string"""
        import re
        match = re.search(r'(\d+)°C', weather_string)
        return int(match.group(1)) if match else 22

    def _get_weather_advice(self, weather):
        """Get travel advice based on weather"""
        if 'Sunny' in weather or 'Hot' in weather:
            return "☀️ Perfect weather for outdoor activities! Don't forget sunscreen and stay hydrated."
        elif 'Cloudy' in weather:
            return "☁️ Great for sightseeing. Bring a light jacket just in case."
        elif 'Cool' in weather or 'Mild' in weather:
            return "🍂 Comfortable weather for exploring. Layered clothing recommended."
        elif 'Rain' in weather:
            return "🌧️ Pack an umbrella and waterproof jacket. Indoor activities recommended."
        else:
            return "🌤️ Good travel conditions. Check local forecast for updates."

    # ==================== DESTINATION RECOMMENDATIONS ====================

    def get_destination_recommendations(self, preferences=None, budget=None, category=None):
        """Get personalized destination recommendations"""
        recommendations = []

        for key, city in self.city_database.items():
            score = 0
            reasons = []

            # Check category match
            if category and city['category'] == category:
                score += 3
                reasons.append(f"Perfect {city['category']} destination")

            # Check budget match
            if budget and city['budget'] == budget:
                score += 2
                reasons.append(f"Fits your {budget} budget (${city['price_per_day']}/day)")

            # Check preferences
            if preferences:
                pref_lower = preferences.lower()
                if city['category'] in pref_lower:
                    score += 2
                    reasons.append(f"Matches your interest in {city['category']} travel")

                # Check attractions match
                for attraction in city['attractions'][:2]:
                    if attraction.lower() in pref_lower:
                        score += 1
                        reasons.append(f"Offers {attraction}")

            if score > 0:
                recommendations.append({
                    'name': city['name'],
                    'country': city['country'],
                    'category': city['category'],
                    'budget': city['budget'],
                    'price': city['price_per_day'],
                    'weather': city['weather'],
                    'best_time': city['best_time'],
                    'attractions': city['attractions'][:3],
                    'score': score,
                    'reasons': reasons[:2]
                })

        # Sort by score
        recommendations.sort(key=lambda x: x['score'], reverse=True)
        return recommendations[:5]

    # ==================== PROFESSIONAL CHAT RESPONSES ====================

    def get_professional_chat_response(self, message, context=None):
        """Get professional, human-like chat responses"""
        message_lower = message.lower()

        # Weather queries
        if 'weather' in message_lower:
            # Extract city name
            cities = ['dubai', 'tokyo', 'london', 'new york', 'paris', 'bali', 'rome', 'bangkok', 'istanbul', 'sydney']
            for city in cities:
                if city in message_lower:
                    result = self.get_city_weather(city)
                    if result['success']:
                        return self._format_weather_response(result)

            # If no specific city, show all
            return self._format_all_weather_response()

        # Destination recommendations
        if 'recommend' in message_lower or 'suggest' in message_lower or 'best' in message_lower:
            # Detect preferences
            preferences = []
            if 'beach' in message_lower:
                preferences.append('beach')
            if 'mountain' in message_lower:
                preferences.append('mountain')
            if 'city' in message_lower:
                preferences.append('city')
            if 'historical' in message_lower:
                preferences.append('historical')

            budget = None
            if 'budget' in message_lower or 'cheap' in message_lower:
                budget = 'budget'
            elif 'luxury' in message_lower:
                budget = 'luxury'

            recommendations = self.get_destination_recommendations(
                preferences=message_lower if preferences else None,
                budget=budget
            )

            return self._format_recommendations_response(recommendations, preferences, budget)

        # Budget queries
        if 'budget' in message_lower or 'cheap' in message_lower or 'affordable' in message_lower:
            return self._format_budget_response(message_lower)

        # Itinerary requests
        if 'itinerary' in message_lower or 'plan' in message_lower:
            return self._format_itinerary_help()

        # Booking help
        if 'book' in message_lower:
            return self._format_booking_help()

        # Default professional response
        return self._format_default_response()

    def _format_weather_response(self, weather_data):
        """Format weather response professionally"""
        return f"""☁️ **Weather in {weather_data['city']}, {weather_data['country']}** ☁️

🌡️ **Current:** {weather_data['weather']}
📋 **Details:** {weather_data['weather_detail']}
📅 **Best Time to Visit:** {weather_data['best_time']}

💡 **Travel Tip:** {weather_data['advice']}

✨ **What to do in {weather_data['city']}?**
Tell me "recommend things to do in {weather_data['city']}" for activity suggestions!"""

    def _format_all_weather_response(self):
        """Format all cities weather response"""
        weather_list = self.get_all_weather()
        response = "🌍 **World Weather Update** 🌍\n\n"

        for city in weather_list[:8]:  # Show top 8 cities
            response += f"**{city['city']}** ({city['country']}): {city['weather']}\n"

        response += "\n💡 **Tip:** For detailed weather info, ask: \"What's the weather in Dubai?\""
        return response

    def _format_recommendations_response(self, recommendations, preferences, budget):
        """Format recommendations professionally"""
        if not recommendations:
            return "🌟 **Personalized Recommendations**\n\nI couldn't find exact matches. Try:\n• \"Recommend beach destinations\"\n• \"Budget-friendly cities\"\n• \"Best places for adventure\""

        response = "🌟 **Personalized Travel Recommendations** 🌟\n\n"

        if preferences:
            response += f"✨ Based on your interest in **{', '.join(preferences)}** travel:\n\n"
        elif budget:
            response += f"💰 **{budget.upper()} Travel Options:**\n\n"
        else:
            response += "🏆 **Top Picks for You:**\n\n"

        for rec in recommendations:
            response += f"🏝️ **{rec['name']}, {rec['country']}**\n"
            response += f"   • Category: {rec['category'].title()} | Budget: {rec['budget'].title()}\n"
            response += f"   • Price: ${rec['price']}/day\n"
            response += f"   • Weather: {rec['weather']}\n"
            response += f"   • Best Time: {rec['best_time']}\n"
            response += f"   • Top Attractions: {', '.join(rec['attractions'][:2])}\n"
            response += f"   • ✨ {rec['reasons'][0]}\n\n"

        response += "💡 **How to Book:**\n"
        response += "   Reply: \"Book [destination] on [YYYY-MM-DD] for [people]\"\n"
        response += "   Example: \"Book Paris on 2025-06-15 for 2 people\""

        return response

    def _format_budget_response(self, message_lower):
        """Format budget recommendations"""
        budget_type = 'budget'
        if 'moderate' in message_lower or 'mid' in message_lower:
            budget_type = 'moderate'
        elif 'luxury' in message_lower:
            budget_type = 'luxury'

        recommendations = self.get_destination_recommendations(budget=budget_type)

        response = f"💰 **{budget_type.upper()} Travel Guide** 💰\n\n"

        if recommendations:
            response += f"**Top {budget_type} destinations with daily costs:**\n\n"
            for rec in recommendations[:4]:
                response += f"• **{rec['name']}**: ${rec['price']}/day\n"
                response += f"  ✨ {rec['reasons'][0] if rec['reasons'] else 'Great value!'}\n"

        response += "\n💡 **Money-Saving Tips:**\n"
        response += "• Book flights 2-3 months in advance\n"
        response += "• Travel during shoulder season\n"
        response += "• Use public transportation\n"
        response += "• Eat where locals eat\n"

        return response

    def _format_itinerary_help(self):
        """Format itinerary help response"""
        return """🎒 **Plan Your Perfect Trip** 🎒

I can help you create a personalized itinerary! Tell me:

📍 **Destination:** (e.g., Paris, Tokyo, Bali)
📅 **Duration:** (e.g., 5 days, 1 week)
🎯 **Interests:** (e.g., food, culture, adventure)

**Example:**
"Create a 5-day itinerary for Tokyo with food and culture focus"

Would you like me to create an itinerary for you?"""

    def _format_booking_help(self):
        """Format booking help response"""
        return """✈️ **Ready to Book?** ✈️

I can help you book:
• 🏖️ **Destinations** - Beach, Mountain, City, Historical
• 🏨 **Hotels** - Budget to Luxury options
• ✈️ **Flights** - Domestic and International
• 🎒 **Packages** - All-inclusive deals

**How to Book:**
1. Tell me what you want: "Book Paris on 2025-06-15 for 2 people"
2. I'll show you available options
3. Confirm your booking

**Quick Examples:**
• "Book Dubai on 2025-07-10 for 2 people"
• "Find hotels in London under $200"
• "Show me flights to Tokyo"

What would you like to book today?"""

    def _format_default_response(self):
        """Format default professional response"""
        return """🌟 **Welcome to Tower Travel AI Assistant** 🌟

I'm your personal travel expert! I can help you with:

✈️ **Book Travel**
   • Destinations, Hotels, Flights, Packages

🌍 **Get Recommendations**
   • Based on your preferences and budget
   • Best time to visit
   • Top attractions

☁️ **Weather Updates**
   • Current conditions worldwide
   • Best seasons to travel

💰 **Budget Planning**
   • Find affordable options
   • Money-saving tips

🎒 **Itinerary Planning**
   • Custom travel plans
   • Activity suggestions

**Try these commands:**
• "Weather in Dubai"
• "Recommend beach destinations"
• "Budget-friendly cities"
• "Best time to visit Paris"
• "Create itinerary for Tokyo"

What would you like to explore today?"""

    # ==================== SENTIMENT ANALYSIS ====================

    def analyze_sentiment(self, text):
        """Analyze sentiment using real AI if available, else fallback"""

        # Try real AI first
        if self.use_real_ai:
            try:
                # Try local model first (if loaded)
                if hasattr(self, 'sentiment_pipeline') and self.sentiment_pipeline:
                    result = self.sentiment_pipeline(text)[0]
                    return {
                        'sentiment': result['label'],
                        'confidence': result['score'],
                        'is_positive': result['label'] == 'POSITIVE',
                        'ai_source': 'real_local'
                    }

                # Try API if key exists
                if self.api_key:
                    result = self._call_huggingface_api(
                        "distilbert-base-uncased-finetuned-sst-2-english",
                        text
                    )
                    if result:
                        return {
                            'sentiment': result[0]['label'],
                            'confidence': result[0]['score'],
                            'is_positive': result[0]['label'] == 'POSITIVE',
                            'ai_source': 'real_api'
                        }
            except Exception as e:
                print(f"Error in real AI: {e}")
                pass

        # Fallback to simulated AI
        return self._simulate_sentiment(text)

    def _simulate_sentiment(self, text):
        """Simulated sentiment analysis for fallback"""
        positive_words = ['good', 'great', 'amazing', 'excellent', 'wonderful', 'fantastic',
                          'beautiful', 'love', 'enjoyed', 'perfect', 'awesome', 'best']
        negative_words = ['bad', 'poor', 'terrible', 'awful', 'disappointing', 'hate',
                          'worst', 'waste', 'boring', 'overpriced', 'horrible']

        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)

        if positive_count > negative_count:
            sentiment = 'POSITIVE'
            confidence = min(0.7 + (positive_count * 0.05), 0.95)
        elif negative_count > positive_count:
            sentiment = 'NEGATIVE'
            confidence = min(0.7 + (negative_count * 0.05), 0.95)
        else:
            sentiment = 'NEUTRAL'
            confidence = 0.6

        return {
            'sentiment': sentiment,
            'confidence': confidence,
            'is_positive': sentiment == 'POSITIVE',
            'ai_source': 'simulated'
        }

    # ==================== STATUS CHECK ====================

    def get_status(self):
        """Get current AI status"""
        return {
            'real_ai_enabled': self.use_real_ai,
            'models_loaded': self.models_loaded,
            'api_key_available': bool(self.api_key),
            'ai_source': 'real' if self.use_real_ai else 'simulated',
            'cities_available': len(self.city_database)
        }


# Create global instance
hybrid_ai = HybridHuggingFaceAI()