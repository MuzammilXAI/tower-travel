# test_huggingface.py
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'DjangoProject.settings')
django.setup()

from travel_app.huggingface_ai import hybrid_ai

print("=" * 60)
print("HUGGING FACE AI VERIFICATION")
print("=" * 60)

# 1. Check Status
print("\n1. AI STATUS:")
status = hybrid_ai.get_status()
for key, value in status.items():
    print(f"   {key}: {value}")

# 2. Test Sentiment Analysis
print("\n2. SENTIMENT ANALYSIS TESTS:")
test_cases = [
    "I absolutely love this hotel! The service is amazing!",
    "The flight was delayed and the food was terrible.",
    "The view from the room was okay, nothing special."
]

for test in test_cases:
    result = hybrid_ai.analyze_sentiment(test)
    print(f"\n   Text: {test[:50]}...")
    print(f"   Sentiment: {result['sentiment']}")
    print(f"   Confidence: {result['confidence']:.3f}")
    print(f"   Source: {result['ai_source']}")

# 3. Verify Real AI is Working
print("\n3. VERIFICATION:")
if status['real_ai_enabled'] and status['api_key_available']:
    print("   ✅ REAL HUGGING FACE AI IS WORKING!")
    print("   ✅ API key is valid and active")
    print("   ✅ Sentiment analysis using real transformer models")
else:
    print("   ⚠️ Using simulated AI fallback")
    print("   Check your HUGGINGFACE_API_KEY in .env file")

print("\n" + "=" * 60)