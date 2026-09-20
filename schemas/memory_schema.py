MEMORY_EXTRACTION_FORMAT={
    "format": {
        "type": "json_schema",
        "name": "memory_extraction",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "memories": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "operation":{
                                "type": "string",
                                "enum": [
                                    "add",
                                    "update",
                                    "delete"
                                ]
                            },
                            "key": {
                                "type": "string"
                            },
                            "value": {
                                "type": "string"
                            }
                        },
                        "required": [
                            "operation",
                            "key",
                            "value"
                        ],
                        "additionalProperties": False
                    }
                }
            },
            "required": [
                "memories"
            ],
            "additionalProperties": False
        }
    }
}