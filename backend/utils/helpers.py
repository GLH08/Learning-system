import json
from typing import Any, Optional, Dict, List


def to_json(data: Any) -> Optional[str]:
    """Convert data to JSON string"""
    if data is None:
        return None
    return json.dumps(data, ensure_ascii=False)


def from_json(json_str: Optional[str], default: Any = None) -> Any:
    """Parse JSON string to data"""
    if not json_str:
        return default
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return default


def snake_to_camel(snake_str: str) -> str:
    """Convert snake_case to camelCase"""
    components = snake_str.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])


def camel_to_snake(camel_str: str) -> str:
    """Convert camelCase to snake_case"""
    result = []
    for i, char in enumerate(camel_str):
        if char.isupper() and i > 0:
            result.append('_')
        result.append(char.lower())
    return ''.join(result)


def dict_to_camel(data: Dict) -> Dict:
    """Convert dict keys from snake_case to camelCase"""
    if not isinstance(data, dict):
        return data
    
    result = {}
    for key, value in data.items():
        camel_key = snake_to_camel(key)
        if isinstance(value, dict):
            result[camel_key] = dict_to_camel(value)
        elif isinstance(value, list):
            result[camel_key] = [dict_to_camel(item) if isinstance(item, dict) else item for item in value]
        else:
            result[camel_key] = value
    return result


def dict_to_snake(data: Dict) -> Dict:
    """Convert dict keys from camelCase to snake_case"""
    if not isinstance(data, dict):
        return data
    
    result = {}
    for key, value in data.items():
        snake_key = camel_to_snake(key)
        if isinstance(value, dict):
            result[snake_key] = dict_to_snake(value)
        elif isinstance(value, list):
            result[snake_key] = [dict_to_snake(item) if isinstance(item, dict) else item for item in value]
        else:
            result[snake_key] = value
    return result
