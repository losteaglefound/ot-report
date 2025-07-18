#!/usr/bin/env python3
"""
PediEAT Age-Based Evaluation System
Uses official reference values to determine concern levels based on child's age.
"""

import json
from typing import List, Dict, Any, Optional


def get_pedieat_reference_values() -> Dict[str, Any]:
    """
    Get PediEAT reference values for all age groups.
    
    Returns:
        dict: Complete reference data for all age groups
    """
    
    reference_data = {
        "6-9_months": {
            "age_range": "6 months 0 days - 9 months 0 days",
            "domains": {
                "PHYSIOLOGIC SYMPTOMS": {
                    "no_concern": "<27",
                    "concern": "27-31", 
                    "high_concern": "32-135"
                },
                "PROBLEMATIC MEALTIME BEHAVIORS": {
                    "no_concern": "<30",
                    "concern": "30-36",
                    "high_concern": "37-115"
                },
                "SELECTIVE RESTRICTIVE EATING": {
                    "no_concern": "<26",
                    "concern": "26-27",
                    "high_concern": "28-75"
                },
                "ORAL PROCESSING": {
                    "no_concern": "<37",
                    "concern": "37-42",
                    "high_concern": "43-65"
                },
                "TOTAL SCORE": {
                    "no_concern": "<101",
                    "concern": "101-116",
                    "high_concern": "117-390"
                }
            }
        },
        "9-12_months": {
            "age_range": "9 months 1 day - 12 months 0 days",
            "domains": {
                "PHYSIOLOGIC SYMPTOMS": {
                    "no_concern": "<24",
                    "concern": "24-31",
                    "high_concern": "32-135"
                },
                "PROBLEMATIC MEALTIME BEHAVIORS": {
                    "no_concern": "<32",
                    "concern": "32-38",
                    "high_concern": "39-115"
                },
                "SELECTIVE RESTRICTIVE EATING": {
                    "no_concern": "<27",
                    "concern": "27-31",
                    "high_concern": "32-75"
                },
                "ORAL PROCESSING": {
                    "no_concern": "<32",
                    "concern": "32-37",
                    "high_concern": "38-65"
                },
                "TOTAL SCORE": {
                    "no_concern": "<102",
                    "concern": "102-124",
                    "high_concern": "125-390"
                }
            }
        },
        "12-15_months": {
            "age_range": "12 months 1 day - 15 months 0 days",
            "domains": {
                "PHYSIOLOGIC SYMPTOMS": {
                    "no_concern": "<29",
                    "concern": "29-34",
                    "high_concern": "35-135"
                },
                "PROBLEMATIC MEALTIME BEHAVIORS": {
                    "no_concern": "<38",
                    "concern": "38-46",
                    "high_concern": "47-115"
                },
                "SELECTIVE RESTRICTIVE EATING": {
                    "no_concern": "<28",
                    "concern": "28-31",
                    "high_concern": "32-75"
                },
                "ORAL PROCESSING": {
                    "no_concern": "<31",
                    "concern": "31-35",
                    "high_concern": "36-65"
                },
                "TOTAL SCORE": {
                    "no_concern": "<107",
                    "concern": "107-125",
                    "high_concern": "126-390"
                }
            }
        },
        "15-18_months": {
            "age_range": "15 months 1 day - 18 months 0 days",
            "domains": {
                "PHYSIOLOGIC SYMPTOMS": {
                    "no_concern": "<17",
                    "concern": "17-20",
                    "high_concern": "21-135"
                },
                "PROBLEMATIC MEALTIME BEHAVIORS": {
                    "no_concern": "<38",
                    "concern": "38-44",
                    "high_concern": "45-115"
                },
                "SELECTIVE RESTRICTIVE EATING": {
                    "no_concern": "<26",
                    "concern": "26-28",
                    "high_concern": "29-75"
                },
                "ORAL PROCESSING": {
                    "no_concern": "<29",
                    "concern": "29-32",
                    "high_concern": "33-65"
                },
                "TOTAL SCORE": {
                    "no_concern": "<98",
                    "concern": "98-110",
                    "high_concern": "111-390"
                }
            }
        },
        "18-24_months": {
            "age_range": "18 months 1 day - 24 months 0 days",
            "domains": {
                "PHYSIOLOGIC SYMPTOMS": {
                    "no_concern": "<16",
                    "concern": "16-22",
                    "high_concern": "23-135"
                },
                "PROBLEMATIC MEALTIME BEHAVIORS": {
                    "no_concern": "<43",
                    "concern": "43-48",
                    "high_concern": "49-115"
                },
                "SELECTIVE RESTRICTIVE EATING": {
                    "no_concern": "<22",
                    "concern": "22-27",
                    "high_concern": "28-75"
                },
                "ORAL PROCESSING": {
                    "no_concern": "<24",
                    "concern": "24-30",
                    "high_concern": "31-65"
                },
                "TOTAL SCORE": {
                    "no_concern": "<97",
                    "concern": "97-107",
                    "high_concern": "108-390"
                }
            }
        },
        "2-2.5_years": {
            "age_range": "2 years 1 day - 2.5 years 0 days",
            "domains": {
                "PHYSIOLOGIC SYMPTOMS": {
                    "no_concern": "<18",
                    "concern": "18-21",
                    "high_concern": "22-135"
                },
                "PROBLEMATIC MEALTIME BEHAVIORS": {
                    "no_concern": "<47",
                    "concern": "47-48",
                    "high_concern": "49-115"
                },
                "SELECTIVE RESTRICTIVE EATING": {
                    "no_concern": "<23",
                    "concern": "23-28",
                    "high_concern": "29-75"
                },
                "ORAL PROCESSING": {
                    "no_concern": "<27",
                    "concern": "27-33",
                    "high_concern": "34-65"
                },
                "TOTAL SCORE": {
                    "no_concern": "<106",
                    "concern": "106-120",
                    "high_concern": "121-390"
                }
            }
        },
        "2.5-3_years": {
            "age_range": "2.5 years 1 day - 3 years 0 days",
            "domains": {
                "PHYSIOLOGIC SYMPTOMS": {
                    "no_concern": "<15",
                    "concern": "15-22",
                    "high_concern": "23-135"
                },
                "PROBLEMATIC MEALTIME BEHAVIORS": {
                    "no_concern": "<54",
                    "concern": "54-60",
                    "high_concern": "61-115"
                },
                "SELECTIVE RESTRICTIVE EATING": {
                    "no_concern": "<21",
                    "concern": "21-25",
                    "high_concern": "26-75"
                },
                "ORAL PROCESSING": {
                    "no_concern": "<26",
                    "concern": "26-29",
                    "high_concern": "30-65"
                },
                "TOTAL SCORE": {
                    "no_concern": "<109",
                    "concern": "109-119",
                    "high_concern": "120-390"
                }
            }
        },
        "3-4_years": {
            "age_range": "3 years 1 day - 4 years 0 days",
            "domains": {
                "PHYSIOLOGIC SYMPTOMS": {
                    "no_concern": "<16",
                    "concern": "16-19",
                    "high_concern": "20-135"
                },
                "PROBLEMATIC MEALTIME BEHAVIORS": {
                    "no_concern": "<51",
                    "concern": "51-55",
                    "high_concern": "56-115"
                },
                "SELECTIVE RESTRICTIVE EATING": {
                    "no_concern": "<20",
                    "concern": "20-22",
                    "high_concern": "23-75"
                },
                "ORAL PROCESSING": {
                    "no_concern": "<27",
                    "concern": "27-29",
                    "high_concern": "30-65"
                },
                "TOTAL SCORE": {
                    "no_concern": "<106",
                    "concern": "106-112",
                    "high_concern": "113-390"
                }
            }
        },
        "4-5_years": {
            "age_range": "4 years 1 day - 5 years 0 days",
            "domains": {
                "PHYSIOLOGIC SYMPTOMS": {
                    "no_concern": "<16",
                    "concern": "16-19",
                    "high_concern": "20-135"
                },
                "PROBLEMATIC MEALTIME BEHAVIORS": {
                    "no_concern": "<51",
                    "concern": "51-57",
                    "high_concern": "58-115"
                },
                "SELECTIVE RESTRICTIVE EATING": {
                    "no_concern": "<19",
                    "concern": "19-21",
                    "high_concern": "22-75"
                },
                "ORAL PROCESSING": {
                    "no_concern": "<24",
                    "concern": "24-27",
                    "high_concern": "28-65"
                },
                "TOTAL SCORE": {
                    "no_concern": "<102",
                    "concern": "102-114",
                    "high_concern": "115-390"
                }
            }
        },
        "5-6_years": {
            "age_range": "5 years 1 day - 6 years 0 days",
            "domains": {
                "PHYSIOLOGIC SYMPTOMS": {
                    "no_concern": "<14",
                    "concern": "14-19",
                    "high_concern": "20-135"
                },
                "PROBLEMATIC MEALTIME BEHAVIORS": {
                    "no_concern": "<51",
                    "concern": "51-54",
                    "high_concern": "55-115"
                },
                "SELECTIVE RESTRICTIVE EATING": {
                    "no_concern": "<16",
                    "concern": "16-22",
                    "high_concern": "23-75"
                },
                "ORAL PROCESSING": {
                    "no_concern": "<22",
                    "concern": "22-26",
                    "high_concern": "27-65"
                },
                "TOTAL SCORE": {
                    "no_concern": "<96",
                    "concern": "96-109",
                    "high_concern": "110-390"
                }
            }
        },
        "6-7_years": {
            "age_range": "6 years 1 day - 7 years 0 days",
            "domains": {
                "PHYSIOLOGIC SYMPTOMS": {
                    "no_concern": "<14",
                    "concern": "14-18",
                    "high_concern": "19-135"
                },
                "PROBLEMATIC MEALTIME BEHAVIORS": {
                    "no_concern": "<42",
                    "concern": "42-47",
                    "high_concern": "48-115"
                },
                "SELECTIVE RESTRICTIVE EATING": {
                    "no_concern": "<19",
                    "concern": "19-20",
                    "high_concern": "21-75"
                },
                "ORAL PROCESSING": {
                    "no_concern": "<23",
                    "concern": "23-27",
                    "high_concern": "28-65"
                },
                "TOTAL SCORE": {
                    "no_concern": "<82",
                    "concern": "82-99",
                    "high_concern": "100-390"
                }
            }
        }
    }
    
    return reference_data


def determine_age_group(age_months: int) -> Optional[str]:
    """
    Determine the appropriate age group for PediEAT evaluation.
    
    Args:
        age_months (int): Child's age in months
        
    Returns:
        str: Age group key or None if out of range
    """
    
    age_mapping = {
        (6, 9): "6-9_months",
        (9, 12): "9-12_months", 
        (12, 15): "12-15_months",
        (15, 18): "15-18_months",
        (18, 24): "18-24_months",
        (24, 30): "2-2.5_years",   # 2-2.5 years
        (30, 36): "2.5-3_years",   # 2.5-3 years
        (36, 48): "3-4_years",     # 3-4 years
        (48, 60): "4-5_years",     # 4-5 years
        (60, 72): "5-6_years",     # 5-6 years
        (72, 84): "6-7_years"      # 6-7 years
    }
    
    for (min_age, max_age), group_key in age_mapping.items():
        if min_age <= age_months < max_age:
            return group_key
    
    return None


def parse_threshold_range(threshold_str: str) -> tuple:
    """
    Parse threshold range string into min/max values.
    
    Args:
        threshold_str (str): Threshold string like "<27", "27-31", "32-135"
        
    Returns:
        tuple: (min_value, max_value, comparison_type)
    """
    
    if threshold_str.startswith("<"):
        # Less than threshold
        value = int(threshold_str[1:])
        return (0, value - 1, "less_than")
    elif "-" in threshold_str:
        # Range threshold
        min_val, max_val = threshold_str.split("-")
        return (int(min_val), int(max_val), "range")
    else:
        # Greater than or equal threshold  
        value = int(threshold_str)
        return (value, 999, "greater_equal")


def determine_concern_level(score: int, domain_thresholds: Dict[str, str]) -> str:
    """
    Determine concern level based on score and thresholds.
    
    Args:
        score (int): Domain score
        domain_thresholds (dict): Thresholds for the domain
        
    Returns:
        str: Concern level ("No Concern", "Concern", "High Concern")
    """
    
    # Parse thresholds
    no_concern_min, no_concern_max, _ = parse_threshold_range(domain_thresholds["no_concern"])
    concern_min, concern_max, _ = parse_threshold_range(domain_thresholds["concern"])
    high_concern_min, high_concern_max, _ = parse_threshold_range(domain_thresholds["high_concern"])
    
    # Determine concern level
    if no_concern_min <= score <= no_concern_max:
        return "No Concern"
    elif concern_min <= score <= concern_max:
        return "Concern"
    elif high_concern_min <= score <= high_concern_max:
        return "High Concern"
    else:
        # Edge case handling
        if score < concern_min:
            return "No Concern"
        else:
            return "High Concern"


def parse_pedieat_domain_scores(pedieat_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Parse PediEAT data and calculate domain scores.
    
    Args:
        pedieat_data (dict): PediEAT data structure
        
    Returns:
        list: List of domain scores
    """
    
    domain_scores = []
    
    # Domain name mapping
    domain_mapping = {
        "physiologic_symtoms": "PHYSIOLOGIC SYMPTOMS",
        "problematic_mealtime_bahaviors": "PROBLEMATIC MEALTIME BEHAVIORS", 
        "selective_restrictive_eating": "SELECTIVE RESTRICTIVE EATING",
        "oral_processing": "ORAL PROCESSING"
    }
    
    for domain_key, domain_data in pedieat_data.items():
        if not isinstance(domain_data, dict):
            continue
            
        # Get asc_scoring and desc_scoring
        asc_scoring = domain_data.get("asc_scoring", {})
        desc_scoring = domain_data.get("desc_scoring", {})
        
        # Extract scores (they're stored as strings in the JSON)
        asc_score = int(asc_scoring.get("score", "0"))
        desc_score = int(desc_scoring.get("score", "0"))
        
        # Calculate total domain score
        total_score = asc_score + desc_score
        
        # Format domain name
        formatted_domain_name = domain_mapping.get(domain_key, domain_key.upper().replace("_", " "))
        
        domain_scores.append({
            "domain": formatted_domain_name,
            "score": total_score,
            "asc_score": asc_score,
            "desc_score": desc_score
        })
    
    return domain_scores


def evaluate_pedieat_by_age(pedieat_data: Dict[str, Any], child_age_months: int) -> List[Dict[str, Any]]:
    """
    Evaluate PediEAT assessment data using age-appropriate reference values.
    
    Args:
        pedieat_data (dict): PediEAT assessment data
        child_age_months (int): Child's age in months
        
    Returns:
        list: List of dictionaries with keys 'domain', 'score', 'status'
    """
    
    # Step 1: Determine age group
    age_group = determine_age_group(child_age_months)
    if not age_group:
        raise ValueError(f"Age {child_age_months} months is outside supported range (6-84 months)")
    
    # Step 2: Get reference values for age group
    reference_data = get_pedieat_reference_values()
    age_thresholds = reference_data[age_group]["domains"]
    
    # Step 3: Parse domain scores
    domain_scores = parse_pedieat_domain_scores(pedieat_data)
    
    # Step 4: Calculate total score
    total_score = sum(domain["score"] for domain in domain_scores)
    
    # Step 5: Evaluate each domain + total
    results = []
    
    # Evaluate individual domains
    for domain in domain_scores:
        domain_name = domain["domain"]
        score = domain["score"]
        
        if domain_name in age_thresholds:
            status = determine_concern_level(score, age_thresholds[domain_name])
        else:
            status = "Unknown"
        
        results.append({
            "domain": domain_name,
            "score": score,
            "status": status
        })
    
    # Evaluate total score
    total_status = determine_concern_level(total_score, age_thresholds["TOTAL SCORE"])
    results.append({
        "domain": "TOTAL SCORE",
        "score": total_score,
        "status": total_status
    })
    
    return results


def get_age_group_info(child_age_months: int) -> Dict[str, Any]:
    """
    Get information about the age group for a given age.
    
    Args:
        child_age_months (int): Child's age in months
        
    Returns:
        dict: Age group information
    """
    
    age_group = determine_age_group(child_age_months)
    if not age_group:
        return {"error": f"Age {child_age_months} months is outside supported range"}
    
    reference_data = get_pedieat_reference_values()
    age_info = reference_data[age_group]
    
    return {
        "age_group_key": age_group,
        "age_range": age_info["age_range"],
        "child_age_months": child_age_months,
        "thresholds": age_info["domains"]
    }


def parse_pedieat_domain_scores(report_data):
    sample_pedieat_data = report_data.get("extracted_data", {}).get("pedieat", {})
    age = report_data.get("patient_info", {}).get("chronological_age", {}).get('total_months')
    print("###############", age, sample_pedieat_data)

    try:

        print(f"\n👶 Child Age: {age} months")
        print("-" * 40)
        
        # Get age group info
        age_info = get_age_group_info(age)
        print(f"📊 Age Group: {age_info['age_group_key']} ({age_info['age_range']})")
        
        # Evaluate PediEAT data
        results = evaluate_pedieat_by_age(sample_pedieat_data, age)
        
        print("📋 Evaluation Results:")
        for result in results:
            print(f"  • {result['domain']}: {result['score']} → {result['status']}")
        
        print(f"\n📄 JSON Format:")
        print(json.dumps(results, indent=2))


        print(f"\n💡 Supported Age Range: 6-84 months (0.5-7 years)")
        print(f"📚 Reference: Official PediEAT Assessment Tool tables") 

        return results
        
    except ValueError as e:
        print(f"❌ Error: {e}")
        return {}


# Example usage and testing
if __name__ == "__main__":
    
    with open("/home/lap-49/Documents/ot-report/outputs/report_data_56b6bede-bbfd-454b-9dfa-3ec5d1911898.json", 'r') as f:
        report_data = json.loads(f.read())

    sample_pedieat_data = report_data.get("extracted_data", {}).get("pedieat")
    
    # Test with different ages
    test_ages = [34]  # months
    
    for age in test_ages:
        print(f"\n👶 Child Age: {age} months")
        print("-" * 40)
        
        try:
            # Get age group info
            age_info = get_age_group_info(age)
            print(f"📊 Age Group: {age_info['age_group_key']} ({age_info['age_range']})")
            
            # Evaluate PediEAT data
            results = evaluate_pedieat_by_age(sample_pedieat_data, age)
            
            print("📋 Evaluation Results:")
            for result in results:
                print(f"  • {result['domain']}: {result['score']} → {result['status']}")
            
            print(f"\n📄 JSON Format:")
            print(json.dumps(results, indent=2))
            
        except ValueError as e:
            print(f"❌ Error: {e}")
    
    print(f"\n💡 Supported Age Range: 6-84 months (0.5-7 years)")
    print(f"📚 Reference: Official PediEAT Assessment Tool tables") 