import json


# from sconfig import config as script_config
from config import config as server_config




def parse_chomps_reference_values():
    """
    Parse ChOMPS reference values for all age groups and extract concern metrics.
    
    Returns:
        dict: Dictionary containing concern thresholds for each age group and domain
    """
    
    chomps_reference_data = {
        "6-9_months": {
            "age_range": "6 months 0 days - 9 months 0 days",
            "domains": {
                "COMPLEX MOVEMENT PATTERNS": {
                    "no_concern": "Not Applicable",
                    "concern": "Not Applicable", 
                    "high_concern": "Not Applicable"
                },
                "BASIC MOVEMENT PATTERNS": {
                    "no_concern": "26-40",
                    "concern": "24-25",
                    "high_concern": "<24"
                },
                "ORAL-MOTOR COORDINATION": {
                    "no_concern": "9-28",
                    "concern": "7-8", 
                    "high_concern": "<7"
                },
                "FUNDAMENTAL ORAL-MOTOR SKILLS": {
                    "no_concern": "8-12",
                    "concern": "6-7",
                    "high_concern": "<6"
                },
                "TOTAL SCORE": {
                    "no_concern": "45-80",
                    "concern": "39-45",
                    "high_concern": "<39"
                }
            }
        },
        
        "9-12_months": {
            "age_range": "9 months 1 day - 12 months 0 days",
            "domains": {
                "COMPLEX MOVEMENT PATTERNS": {
                    "no_concern": "4-46",
                    "concern": "2-3",
                    "high_concern": "<2"
                },
                "BASIC MOVEMENT PATTERNS": {
                    "no_concern": "37-40",
                    "concern": "32-36",
                    "high_concern": "<32"
                },
                "ORAL-MOTOR COORDINATION": {
                    "no_concern": "21-28",
                    "concern": "17-20",
                    "high_concern": "<17"
                },
                "FUNDAMENTAL ORAL-MOTOR SKILLS": {
                    "no_concern": "10-12",
                    "concern": "8-9",
                    "high_concern": "<8"
                },
                "TOTAL SCORE": {
                    "no_concern": "74-126",
                    "concern": "69-73",
                    "high_concern": "<69"
                }
            }
        },
        
        "12-15_months": {
            "age_range": "12 months 1 day - 15 months 0 days",
            "domains": {
                "COMPLEX MOVEMENT PATTERNS": {
                    "no_concern": "10-46",
                    "concern": "6-9",
                    "high_concern": "<6"
                },
                "BASIC MOVEMENT PATTERNS": {
                    "no_concern": "40",
                    "concern": "38-39",
                    "high_concern": "<38"
                },
                "ORAL-MOTOR COORDINATION": {
                    "no_concern": "24-28",
                    "concern": "20-23",
                    "high_concern": "<20"
                },
                "FUNDAMENTAL ORAL-MOTOR SKILLS": {
                    "no_concern": "11-12",
                    "concern": "9-10",
                    "high_concern": "<9"
                },
                "TOTAL SCORE": {
                    "no_concern": "85-126",
                    "concern": "78-84",
                    "high_concern": "<78"
                }
            }
        },
        
        "15-18_months": {
            "age_range": "15 months 1 day - 18 months 0 days",
            "domains": {
                "COMPLEX MOVEMENT PATTERNS": {
                    "no_concern": "20-46",
                    "concern": "16-19",
                    "high_concern": "<16"
                },
                "BASIC MOVEMENT PATTERNS": {
                    "no_concern": "40",
                    "concern": "38-39",
                    "high_concern": "<38"
                },
                "ORAL-MOTOR COORDINATION": {
                    "no_concern": "27-28",
                    "concern": "25-26",
                    "high_concern": "<25"
                },
                "FUNDAMENTAL ORAL-MOTOR SKILLS": {
                    "no_concern": "12",
                    "concern": "10-11",
                    "high_concern": "<10"
                },
                "TOTAL SCORE": {
                    "no_concern": "97-126",
                    "concern": "92-96",
                    "high_concern": "<92"
                }
            }
        },
        
        "18-24_months": {
            "age_range": "18 months 1 day - 24 months 0 days",
            "domains": {
                "COMPLEX MOVEMENT PATTERNS": {
                    "no_concern": "25-46",
                    "concern": "21-24",
                    "high_concern": "<21"
                },
                "BASIC MOVEMENT PATTERNS": {
                    "no_concern": "40",
                    "concern": "<40",
                    "high_concern": "<40"
                },
                "ORAL-MOTOR COORDINATION": {
                    "no_concern": "27-28",
                    "concern": "25-26",
                    "high_concern": "<25"
                },
                "FUNDAMENTAL ORAL-MOTOR SKILLS": {
                    "no_concern": "12",
                    "concern": "11",
                    "high_concern": "<11"
                },
                "TOTAL SCORE": {
                    "no_concern": "104-126",
                    "concern": "101-103",
                    "high_concern": "<101"
                }
            }
        },
        
        "2-2.5_years": {
            "age_range": "2 years 1 day - 2.5 years old",
            "domains": {
                "COMPLEX MOVEMENT PATTERNS": {
                    "no_concern": "34-46",
                    "concern": "32-33",
                    "high_concern": "<32"
                },
                "BASIC MOVEMENT PATTERNS": {
                    "no_concern": "40",
                    "concern": "<40",
                    "high_concern": "<40"
                },
                "ORAL-MOTOR COORDINATION": {
                    "no_concern": "28",
                    "concern": "26-27",
                    "high_concern": "<26"
                },
                "FUNDAMENTAL ORAL-MOTOR SKILLS": {
                    "no_concern": "12",
                    "concern": "11",
                    "high_concern": "<11"
                },
                "TOTAL SCORE": {
                    "no_concern": "113-126",
                    "concern": "109-112",
                    "high_concern": "<109"
                }
            }
        },
        
        "2.5-3_years": {
            "age_range": "2.5 years 1 day - 3 years old",
            "domains": {
                "COMPLEX MOVEMENT PATTERNS": {
                    "no_concern": "41-46",
                    "concern": "37-40",
                    "high_concern": "<37"
                },
                "BASIC MOVEMENT PATTERNS": {
                    "no_concern": "40",
                    "concern": "<40",
                    "high_concern": "<40"
                },
                "ORAL-MOTOR COORDINATION": {
                    "no_concern": "28",
                    "concern": "27",
                    "high_concern": "<27"
                },
                "FUNDAMENTAL ORAL-MOTOR SKILLS": {
                    "no_concern": "12",
                    "concern": "11",
                    "high_concern": "<11"
                },
                "TOTAL SCORE": {
                    "no_concern": "121-126",
                    "concern": "117-120",
                    "high_concern": "<117"
                }
            }
        },
        
        "3-4_years": {
            "age_range": "3 years 1 day - 4 years old",
            "domains": {
                "COMPLEX MOVEMENT PATTERNS": {
                    "no_concern": "41-46",
                    "concern": "38-40",
                    "high_concern": "<38"
                },
                "BASIC MOVEMENT PATTERNS": {
                    "no_concern": "40",
                    "concern": "<40",
                    "high_concern": "<40"
                },
                "ORAL-MOTOR COORDINATION": {
                    "no_concern": "28",
                    "concern": "27",
                    "high_concern": "<27"
                },
                "FUNDAMENTAL ORAL-MOTOR SKILLS": {
                    "no_concern": "12",
                    "concern": "<12",
                    "high_concern": "<12"
                },
                "TOTAL SCORE": {
                    "no_concern": "120-126",
                    "concern": "118-119",
                    "high_concern": "<118"
                }
            }
        },
        
        "5-6_years": {
            "age_range": "5 years 1 day - 6 years old",
            "domains": {
                "COMPLEX MOVEMENT PATTERNS": {
                    "no_concern": "45-46",
                    "concern": "42-44",
                    "high_concern": "<42"
                },
                "BASIC MOVEMENT PATTERNS": {
                    "no_concern": "40",
                    "concern": "<40",
                    "high_concern": "<40"
                },
                "ORAL-MOTOR COORDINATION": {
                    "no_concern": "28",
                    "concern": "27",
                    "high_concern": "<27"
                },
                "FUNDAMENTAL ORAL-MOTOR SKILLS": {
                    "no_concern": "12",
                    "concern": "<12",
                    "high_concern": "<12"
                },
                "TOTAL SCORE": {
                    "no_concern": "125-126",
                    "concern": "121-124",
                    "high_concern": "<121"
                }
            }
        },
        
        "6-7_years": {
            "age_range": "6 years 1 day - 7 years old",
            "domains": {
                "COMPLEX MOVEMENT PATTERNS": {
                    "no_concern": "45-46",
                    "concern": "44",
                    "high_concern": "<44"
                },
                "BASIC MOVEMENT PATTERNS": {
                    "no_concern": "40",
                    "concern": "<40",
                    "high_concern": "<40"
                },
                "ORAL-MOTOR COORDINATION": {
                    "no_concern": "28",
                    "concern": "27",
                    "high_concern": "<27"
                },
                "FUNDAMENTAL ORAL-MOTOR SKILLS": {
                    "no_concern": "12",
                    "concern": "<12",
                    "high_concern": "<12"
                },
                "TOTAL SCORE": {
                    "no_concern": "125-126",
                    "concern": "122-124",
                    "high_concern": "<122"
                }
            }
        }
    }
    
    return chomps_reference_data


def get_concern_level_for_score(age_group: str, domain: str, score: int) -> dict:
    """
    Determine the concern level for a given score based on age group and domain.
    
    Args:
        age_group (str): Age group key (e.g., "12-15_months")
        domain (str): Domain name (e.g., "COMPLEX MOVEMENT PATTERNS") 
        score (int): The score to evaluate
        
    Returns:
        dict: Dictionary with concern level and details
    """
    reference_data = parse_chomps_reference_values()
    
    if age_group not in reference_data:
        return {
            "error": f"Age group '{age_group}' not found",
            "available_age_groups": list(reference_data.keys())
        }
    
    if domain not in reference_data[age_group]["domains"]:
        return {
            "error": f"Domain '{domain}' not found for age group '{age_group}'",
            "available_domains": list(reference_data[age_group]["domains"].keys())
        }
    
    domain_data = reference_data[age_group]["domains"][domain]
    
    # Parse ranges and determine concern level
    concern_level = "Unknown"
    percentile_range = "Unknown"
    
    # Check high concern first (most restrictive)
    high_concern = domain_data["high_concern"]
    if _score_in_range(score, high_concern):
        concern_level = "High Concern"
        percentile_range = "<5th%"
    
    # Check concern range
    elif _score_in_range(score, domain_data["concern"]):
        concern_level = "Concern"
        percentile_range = "5th-10th%"
    
    # Check no concern range
    elif _score_in_range(score, domain_data["no_concern"]):
        concern_level = "No Concern"
        percentile_range = ">10th%"
    
    return {
        "age_group": age_group,
        "age_range": reference_data[age_group]["age_range"],
        "domain": domain,
        "score": score,
        "concern_level": concern_level,
        "percentile_range": percentile_range,
        "reference_ranges": domain_data
    }


def _score_in_range(score: int, range_str: str) -> bool:
    """
    Check if a score falls within a given range string.
    
    Args:
        score (int): Score to check
        range_str (str): Range string (e.g., "26-40", "<24", "Not Applicable")
        
    Returns:
        bool: True if score is in range, False otherwise
    """
    if range_str == "Not Applicable":
        return False
    
    # Handle less than cases
    if range_str.startswith("<"):
        threshold = int(range_str[1:])
        return score < threshold
    
    # Handle single values
    if "-" not in range_str:
        try:
            return score == int(range_str)
        except ValueError:
            return False
    
    # Handle ranges
    try:
        parts = range_str.split("-")
        if len(parts) == 2:
            min_val = int(parts[0])
            max_val = int(parts[1])
            return min_val <= score <= max_val
    except ValueError:
        return False
    
    return False


def analyze_chomps_scores_by_age(domain_scores: list, child_age_months: int) -> dict:
    """
    Analyze ChOMPS domain scores against age-appropriate reference values.
    
    Args:
        domain_scores (list): List of domain scores from parse_chomps_domain_scores()
        child_age_months (int): Child's age in months
        
    Returns:
        dict: Analysis results with concern levels for each domain
    """
    # Determine appropriate age group
    age_group = _get_age_group_from_months(child_age_months)
    
    if not age_group:
        return {
            "error": f"No reference data available for age {child_age_months} months",
            "child_age_months": child_age_months
        }
    
    analysis_results = {
        "child_age_months": child_age_months,
        "age_group": age_group,
        "domain_analysis": [],
        "overall_concern_level": "No Concern",
        "summary": {
            "no_concern_domains": 0,
            "concern_domains": 0,
            "high_concern_domains": 0
        }
    }
    
    highest_concern = "No Concern"
    
    for domain_score in domain_scores:
        domain_name = domain_score["domain_name"]
        total_score = domain_score["total_score"]
        
        # Get concern level for this domain
        concern_analysis = get_concern_level_for_score(age_group, domain_name, total_score)
        
        analysis_results["domain_analysis"].append(concern_analysis)
        
        # Track summary statistics
        concern_level = concern_analysis.get("concern_level", "Unknown")
        if concern_level == "No Concern":
            analysis_results["summary"]["no_concern_domains"] += 1
        elif concern_level == "Concern":
            analysis_results["summary"]["concern_domains"] += 1
            if highest_concern == "No Concern":
                highest_concern = "Concern"
        elif concern_level == "High Concern":
            analysis_results["summary"]["high_concern_domains"] += 1
            highest_concern = "High Concern"
    
    analysis_results["overall_concern_level"] = highest_concern
    
    return analysis_results


def _get_age_group_from_months(months: int) -> str:
    """
    Determine the appropriate age group key based on age in months.
    
    Args:
        months (int): Age in months
        
    Returns:
        str: Age group key or None if no match
    """
    if 6 <= months <= 9:
        return "6-9_months"
    elif 9 < months <= 12:
        return "9-12_months"
    elif 12 < months <= 15:
        return "12-15_months"
    elif 15 < months <= 18:
        return "15-18_months"
    elif 18 < months <= 24:
        return "18-24_months"
    elif 24 < months <= 30:  # 2-2.5 years
        return "2-2.5_years"
    elif 30 < months <= 36:  # 2.5-3 years
        return "2.5-3_years"
    elif 36 < months <= 48:  # 3-4 years
        return "3-4_years"
    elif 60 < months <= 72:  # 5-6 years
        return "5-6_years"
    elif 72 < months <= 84:  # 6-7 years
        return "6-7_years"
    else:
        return None


def get_all_age_groups() -> list:
    """
    Get list of all available age groups with their details.
    
    Returns:
        list: List of age group information
    """
    reference_data = parse_chomps_reference_values()
    
    age_groups = []
    for key, data in reference_data.items():
        age_groups.append({
            "key": key,
            "age_range": data["age_range"],
            "domains": list(data["domains"].keys())
        })
    
    return age_groups


def extract_age_based_concern_metrics() -> dict:
    """
    Extract age-based concern metrics from ChOMPS reference tables.
    
    Returns:
        dict: Simplified structure with age groups and concern thresholds
    """
    reference_data = parse_chomps_reference_values()
    
    concern_metrics = {}
    
    for age_key, age_data in reference_data.items():
        concern_metrics[age_key] = {
            "age_range": age_data["age_range"],
            "domains": {}
        }
        
        for domain_name, domain_data in age_data["domains"].items():
            concern_metrics[age_key]["domains"][domain_name] = {
                "no_concern_threshold": domain_data["no_concern"],
                "concern_threshold": domain_data["concern"], 
                "high_concern_threshold": domain_data["high_concern"]
            }
    
    return concern_metrics


def get_concern_metrics_for_age_group(age_group: str) -> dict:
    """
    Get concern metrics for a specific age group.
    
    Args:
        age_group (str): Age group key (e.g., "12-15_months")
        
    Returns:
        dict: Concern metrics for the specified age group
    """
    all_metrics = extract_age_based_concern_metrics()
    
    if age_group not in all_metrics:
        return {
            "error": f"Age group '{age_group}' not found",
            "available_age_groups": list(all_metrics.keys())
        }
    
    return all_metrics[age_group]


def analyze_chomps_scores_simple(domain_scores: list, child_age_months: int) -> list:
    """
    Analyze ChOMPS domain scores and return simple JSON structure with status.
    
    Args:
        domain_scores (list): List of domain scores with format [{"domain_name": "", "total_score": int}]
        child_age_months (int): Child's age in months
        
    Returns:
        list: List of dictionaries with format [{"domain_name": "", "score": "", "status": ""}]
    """
    # Determine appropriate age group
    age_group = _get_age_group_from_months(child_age_months)
    
    if not age_group:
        return [{"error": f"No reference data available for age {child_age_months} months"}]
    
    results = []
    
    for domain_score in domain_scores:
        domain_name = domain_score["domain_name"]
        total_score = domain_score["total_score"]
        
        # Get concern level for this domain
        concern_analysis = get_concern_level_for_score(age_group, domain_name, total_score)
        
        # Handle errors (domain not found, etc.)
        if "error" in concern_analysis:
            status = "Unknown"
        else:
            status = concern_analysis.get("concern_level", "Unknown")
        
        results.append({
            "domain_name": domain_name,
            "score": total_score,
            "status": status
        })
    
    return results

def parse_chomps_domain_scores_simple(chomps_observation_data: dict) -> list:
    """
    Simplified version that returns only domain_name and total_score as requested.
    
    Args:
        chomps_data (dict): The CHOMPS observation data with domains and observations
        
    Returns:
        list: List of dictionaries with keys 'domain_name' and 'total_score'
    """
    domain_scores = []
    chomps_data = chomps_observation_data
    
    for domain_name, observations in chomps_data.items():
        # Skip if not a list of observations
        if not isinstance(observations, list):
            continue
            
        # Calculate total score for this domain
        total_score = sum(
            observation.get('score', 0) 
            for observation in observations 
            if isinstance(observation, dict)
        )
        
        # Add domain score to results
        domain_scores.append({
            'domain_name': domain_name,
            'total_score': total_score
        })
    
    return domain_scores


def parse_chomps_domain_scores(report_data: dict):
    
    chomps_observation_data = report_data.get('scores', {}).get("chomps", {}).get("observationsByCategory", {})

    example_scores = parse_chomps_domain_scores_simple(chomps_observation_data)
    print(example_scores)
    
    # Analyze for a 14-month-old child
    child_age = report_data.get("patient_info", {}).get("chronological_age", {}).get("total_months")
    analysis = analyze_chomps_scores_by_age(example_scores, child_age)
    
    print("ChOMPS Analysis Results:")
    print("=" * 50)
    print(json.dumps(analysis, indent=2))
    
    print("\n\nAvailable Age Groups:")
    print("=" * 30)
    age_groups = get_all_age_groups()
    for group in age_groups:
        print(f"Key: {group['key']}")
        print(f"Range: {group['age_range']}")
        print("-" * 30)
    
    # Test the extraction functions
    print("\n\nAge-Based Concern Metrics for 12-15 months:")
    print("=" * 50)
    metrics = get_concern_metrics_for_age_group("12-15_months")
    print(json.dumps(metrics, indent=2))
    
    # Test the simple analysis function (requested format)
    print("\n\nSimple ChOMPS Analysis (Requested Format):")
    print("=" * 50)
    simple_results = analyze_chomps_scores_simple(example_scores, child_age)
    print(json.dumps(simple_results, indent=2)) 

    return simple_results