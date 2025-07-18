#!/usr/bin/env python3
"""
PediEAT Evaluation Demo
Shows how to use the age-based evaluation system with real PediEAT data.
"""

import json
from pedieat_age_based_evaluator import evaluate_pedieat_by_age, get_age_group_info


def demo_pedieat_evaluation():
    """Demonstrate PediEAT evaluation with real data."""
    
    # Your actual PediEAT data from the JSON file
    real_pedieat_data = {
        "physiologic_symtoms": {
            "asc_scoring": {
                "observations": [
                    {"description": "gets watery eyes when eating", "score": "2", "score_string": "Sometimes"},
                    {"description": "gets red color around eyes or face when eating", "score": "0", "score_string": "Never"},
                    {"description": "coughs during or after eating", "score": "2", "score_string": "Sometimes"},
                    {"description": "sounds gurgly or like they need to cough or clear their throat during or after eating", "score": "1", "score_string": "Almost Never"},
                    {"description": "sounds different during or after a meal", "score": "0", "score_string": "Never"},
                    {"description": "chokes or coughs on water or other thin liquids", "score": "2", "score_string": "Sometimes"},
                    {"description": "moves head down toward chest when swallowing", "score": "2", "score_string": "Sometimes"},
                    {"description": "has food or liquid come out of nose when eating", "score": "4", "score_string": "Almost Always"},
                    {"description": "gets pale or blue color around his/her lips during meals", "score": "0", "score_string": "Never"},
                    {"description": "breathes faster or harder when eating", "score": "1", "score_string": "Almost Never"},
                    {"description": "needs to take a break during the meal to rest or catch their breath", "score": "5", "score_string": "Always"},
                    {"description": "gets tired from eating and is not able to finish", "score": "1", "score_string": "Almost Never"},
                    {"description": "sweats/gets clammy during meals", "score": "1", "score_string": "Almost Never"},
                    {"description": "tilts head back while eating", "score": "1", "score_string": "Almost Never"},
                    {"description": "burps more than usual while eating", "score": "1", "score_string": "Almost Never"},
                    {"description": "throws up during mealtime", "score": "0", "score_string": "Never"},
                    {"description": "throws up between meals", "score": "1", "score_string": "Almost Never"},
                    {"description": "arches back during or after meals", "score": "2", "score_string": "Sometimes"},
                    {"description": "gags when it is time to eat", "score": "0", "score_string": "Never"},
                    {"description": "gags with smooth foods like pudding", "score": "0", "score_string": "Never"},
                    {"description": "gags with textured food like coarse oatmeal", "score": "1", "score_string": "Almost Never"},
                    {"description": "gags, coughs, or vomits when brushing teeth", "score": "0", "score_string": "Never"},
                    {"description": "gets a bloated tummy after eating", "score": "1", "score_string": "Almost Never"},
                    {"description": "turns red in face, may cry with stooling", "score": "0", "score_string": "Never"},
                    {"description": "has gas", "score": "0", "score_string": "Never"},
                    {"description": "drools when eating", "score": "3", "score_string": "Often"},
                    {"description": "has a hard time eating due to stuffy nose", "score": "5", "score_string": "Always"}
                ],
                "score": "36"
            },
            "desc_scoring": {
                "observations": [],
                "score": "0"
            }
        },
        "problematic_mealtime_bahaviors": {
            "asc_scoring": {
                "observations": [
                    {"description": "avoids eating by playing or talking", "score": "0", "score_string": "Never"},
                    {"description": "has to be told to start eating", "score": "0", "score_string": "Never"},
                    {"description": "has to be reminded to keep eating", "score": "3", "score_string": "Often"},
                    {"description": "won't eat at meals, but wants food later", "score": "0", "score_string": "Never"},
                    {"description": "stops eating after a few bites", "score": "0", "score_string": "Never"},
                    {"description": "refuses to eat", "score": "0", "score_string": "Never"},
                    {"description": "shows more stress during meals than during non-meal times", "score": "0", "score_string": "Never"},
                    {"description": "insists on food being offered in a certain way", "score": "3", "score_string": "Often"},
                    {"description": "insists on being fed by the same person(s)", "score": "0", "score_string": "Never"},
                    {"description": "becomes upset by the smell of food", "score": "0", "score_string": "Never"},
                    {"description": "throws food or pushes food away", "score": "3", "score_string": "Often"},
                    {"description": "prefers to drink instead of eat", "score": "1", "score_string": "Almost Never"},
                    {"description": "prefers crunchy foods", "score": "0", "score_string": "Never"},
                    {"description": "eats better when entertained", "score": "2", "score_string": "Sometimes"},
                    {"description": "takes more than 30 minutes to eat", "score": "2", "score_string": "Sometimes"},
                    {"description": "needs mealtime to be calm", "score": "2", "score_string": "Sometimes"},
                    {"description": "wants the same food for more than two weeks in a row", "score": "1", "score_string": "Almost Never"}
                ],
                "score": "17"
            },
            "desc_scoring": {
                "observations": [
                    {"description": "likes to eat", "score": "0", "score_string": "Always"},
                    {"description": "eats a variety of foods (fruits, vegetables, proteins, etc.)", "score": "0", "score_string": "Always"},
                    {"description": "is willing to stay seated during mealtime", "score": "0", "score_string": "Always"},
                    {"description": "opens their mouth when food is offered", "score": "0", "score_string": "Always"},
                    {"description": "is willing to touch food with their hands", "score": "0", "score_string": "Always"}
                ],
                "score": "0"
            }
        },
        "selective_restrictive_eating": {
            "asc_scoring": {
                "observations": [
                    {"description": "sniffs food or objects", "score": "0", "score_string": "Never"},
                    {"description": "spits food out", "score": "3", "score_string": "Often"},
                    {"description": "eats too fast", "score": "2", "score_string": "Sometimes"}
                ],
                "score": "5"
            },
            "desc_scoring": {
                "observations": [
                    {"description": "will eat mixed texture foods", "score": "0", "score_string": "Always"},
                    {"description": "will eat food warmer than room temperature", "score": "0", "score_string": "Always"},
                    {"description": "is willing to feed self", "score": "5", "score_string": "Never"},
                    {"description": "keeps food in mouth when eating", "score": "3", "score_string": "Sometimes"},
                    {"description": "keeps liquids in mouth when drinking", "score": "5", "score_string": "Never"},
                    {"description": "keeps their tongue inside mouth during eating", "score": "4", "score_string": "Almost Never"},
                    {"description": "acts hungry before meals", "score": "5", "score_string": "Never"},
                    {"description": "will eat foods that need to be chewed", "score": "2", "score_string": "Often"},
                    {"description": "will eat textured food like coarse oatmeal", "score": "3", "score_string": "Sometimes"},
                    {"description": "will eat frozen food, like ice cream", "score": "5", "score_string": "Never"},
                    {"description": "chews their food enough", "score": "4", "score_string": "Almost Never"},
                    {"description": "moves food in their mouth when chewing without help", "score": "2", "score_string": "Often"}
                ],
                "score": "38"
            }
        },
        "oral_processing": {
            "asc_scoring": {
                "observations": [
                    {"description": "stores food in their cheek or roof of mouth", "score": "2", "score_string": "Sometimes"},
                    {"description": "gets food stuck in their cheek or roof of mouth", "score": "1", "score_string": "Almost Never"},
                    {"description": "prefers smooth foods like yogurt", "score": "1", "score_string": "Almost Never"},
                    {"description": "puts too much food in mouth at one time", "score": "1", "score_string": "Almost Never"},
                    {"description": "puts fingers in mouth to move food", "score": "0", "score_string": "Never"},
                    {"description": "prefers strong flavors", "score": "0", "score_string": "Never"},
                    {"description": "bites down on the spoon or fork and does not release it easily", "score": "3", "score_string": "Often"},
                    {"description": "grinds teeth when awake", "score": "1", "score_string": "Almost Never"},
                    {"description": "chews on toys, clothes, or other objects", "score": "0", "score_string": "Never"},
                    {"description": "has to be reminded to chew food", "score": "2", "score_string": "Sometimes"},
                    {"description": "sucks on food to soften or moisten it, rather than chewing it", "score": "3", "score_string": "Often"},
                    {"description": "chews food but doesn't swallow it", "score": "1", "score_string": "Almost Never"},
                    {"description": "chews a bite of food for a long time", "score": "0", "score_string": "Never"}
                ],
                "score": "15"
            },
            "desc_scoring": {
                "observations": [],
                "score": "0"
            }
        }
    }
    
    print("🍽️ PediEAT Age-Based Evaluation Demo")
    print("=" * 70)
    
    # Example: Evaluate for a 16-month-old child
    child_age = 16  # months
    
    print(f"👶 Child Age: {child_age} months")
    print("-" * 50)
    
    # Get age group information
    age_info = get_age_group_info(child_age)
    print(f"📊 Age Group: {age_info['age_group_key']} ({age_info['age_range']})")
    
    # Evaluate the PediEAT data
    results = evaluate_pedieat_by_age(real_pedieat_data, child_age)
    
    print("\n📋 Evaluation Results:")
    print("-" * 50)
    for result in results:
        icon = "🔴" if result['status'] == "High Concern" else "🟡" if result['status'] == "Concern" else "🟢"
        print(f"{icon} {result['domain']}: {result['score']} → {result['status']}")
    
    print(f"\n📄 Requested JSON Format:")
    print("-" * 50)
    print(json.dumps(results, indent=2))
    
    return results


def evaluate_for_multiple_ages():
    """Show how evaluation changes across different ages."""
    
    # Simplified test data
    test_data = {
        "physiologic_symtoms": {"asc_scoring": {"score": "20"}, "desc_scoring": {"score": "0"}},
        "problematic_mealtime_bahaviors": {"asc_scoring": {"score": "45"}, "desc_scoring": {"score": "0"}},
        "selective_restrictive_eating": {"asc_scoring": {"score": "25"}, "desc_scoring": {"score": "0"}},
        "oral_processing": {"asc_scoring": {"score": "30"}, "desc_scoring": {"score": "0"}}
    }
    
    print("\n\n🔄 Age Comparison Analysis")
    print("=" * 70)
    print("Same scores evaluated across different age groups:")
    
    test_ages = [8, 14, 20, 30, 48, 72]  # Different age groups
    
    for age in test_ages:
        try:
            age_info = get_age_group_info(age)
            results = evaluate_pedieat_by_age(test_data, age)
            
            total_result = next(r for r in results if r['domain'] == 'TOTAL SCORE')
            
            print(f"\n👶 Age {age} months ({age_info['age_group_key']}): Total Score {total_result['score']} → {total_result['status']}")
            
        except ValueError as e:
            print(f"❌ Age {age}: {e}")


if __name__ == "__main__":
    # Run the main demo
    results = demo_pedieat_evaluation()
    
    # Show age comparison
    evaluate_for_multiple_ages()
    
    print("\n" + "=" * 70)
    print("💡 How to use in your code:")
    print("=" * 70)
    print("from pedieat_age_based_evaluator import evaluate_pedieat_by_age")
    print("")
    print("# Your PediEAT data and child's age in months")
    print("results = evaluate_pedieat_by_age(pedieat_data, child_age_months)")
    print("")
    print("# Results format:")
    print("# [{'domain': 'PHYSIOLOGIC SYMPTOMS', 'score': 36, 'status': 'High Concern'}, ...]")
    print("")
    print("🎯 Age ranges supported: 6-84 months (0.5-7 years)")
    print("📚 Based on official PediEAT reference value tables") 