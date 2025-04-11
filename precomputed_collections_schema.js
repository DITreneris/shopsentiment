/**
 * MongoDB Schema definitions for pre-computed collections
 * These collections will store aggregated data to improve dashboard performance
 */

// Precomputed stats collection - general purpose cache
db.createCollection("precomputed_stats", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["type", "identifier", "data", "created_at", "updated_at"],
      properties: {
        type: {
          bsonType: "string",
          description: "Type of stats (e.g., 'keywords', 'sentiment', 'platform')"
        },
        identifier: {
          bsonType: "string",
          description: "Unique identifier for this stats record"
        },
        data: {
          bsonType: "object",
          description: "The pre-computed data"
        },
        created_at: {
          bsonType: "date",
          description: "When this record was first created"
        },
        updated_at: {
          bsonType: "date",
          description: "When this record was last updated"
        },
        expires_at: {
          bsonType: "date",
          description: "When this cache record should expire (optional)"
        }
      }
    }
  }
});

// Create indexes for the precomputed_stats collection
db.precomputed_stats.createIndex({ "type": 1, "identifier": 1 }, { unique: true });
db.precomputed_stats.createIndex({ "updated_at": 1 });
db.precomputed_stats.createIndex({ "expires_at": 1 }, { expireAfterSeconds: 0 });

// Keywords collection - stores pre-computed keyword sentiment analysis
db.createCollection("keyword_stats", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["keyword", "count", "sentiment", "updated_at"],
      properties: {
        keyword: {
          bsonType: "string",
          description: "The keyword text"
        },
        count: {
          bsonType: "int",
          description: "Number of occurrences"
        },
        sentiment: {
          bsonType: "object",
          required: ["score", "label"],
          properties: {
            score: {
              bsonType: "double",
              description: "Average sentiment score (0-1)"
            },
            label: {
              bsonType: "string",
              enum: ["positive", "neutral", "negative"],
              description: "Sentiment category"
            }
          }
        },
        products: {
          bsonType: "array",
          description: "Array of product IDs where this keyword appears",
          items: {
            bsonType: "objectId"
          }
        },
        updated_at: {
          bsonType: "date",
          description: "When this record was last updated"
        }
      }
    }
  }
});

// Create indexes for the keyword_stats collection
db.keyword_stats.createIndex({ "keyword": 1 }, { unique: true });
db.keyword_stats.createIndex({ "count": -1 });
db.keyword_stats.createIndex({ "sentiment.label": 1, "count": -1 });
db.keyword_stats.createIndex({ "updated_at": 1 });

// Time series stats - stores sentiment over time for each product
db.createCollection("time_series_stats", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["product_id", "interval", "data", "updated_at"],
      properties: {
        product_id: {
          bsonType: "objectId",
          description: "Product ID this time series belongs to"
        },
        interval: {
          bsonType: "string",
          enum: ["day", "week", "month"],
          description: "Time grouping interval"
        },
        start_date: {
          bsonType: "date",
          description: "Start date of this time series"
        },
        end_date: {
          bsonType: "date",
          description: "End date of this time series"
        },
        data: {
          bsonType: "array",
          description: "Array of time series data points",
          items: {
            bsonType: "object",
            required: ["date", "sentiments", "total"],
            properties: {
              date: {
                bsonType: "date",
                description: "Date of this data point"
              },
              date_str: {
                bsonType: "string",
                description: "Formatted date string"
              },
              sentiments: {
                bsonType: "object",
                properties: {
                  positive: {
                    bsonType: "object",
                    properties: {
                      count: { bsonType: "int" },
                      percentage: { bsonType: "double" },
                      avg_score: { bsonType: "double" }
                    }
                  },
                  neutral: {
                    bsonType: "object",
                    properties: {
                      count: { bsonType: "int" },
                      percentage: { bsonType: "double" },
                      avg_score: { bsonType: "double" }
                    }
                  },
                  negative: {
                    bsonType: "object",
                    properties: {
                      count: { bsonType: "int" },
                      percentage: { bsonType: "double" },
                      avg_score: { bsonType: "double" }
                    }
                  }
                }
              },
              total: {
                bsonType: "int",
                description: "Total reviews for this period"
              }
            }
          }
        },
        updated_at: {
          bsonType: "date",
          description: "When this record was last updated"
        }
      }
    }
  }
});

// Create indexes for the time_series_stats collection
db.time_series_stats.createIndex({ "product_id": 1, "interval": 1 }, { unique: true });
db.time_series_stats.createIndex({ "updated_at": 1 });

// Platform stats collection - stores rating distribution by platform
db.createCollection("platform_stats", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["_id", "platforms", "updated_at"],
      properties: {
        _id: {
          bsonType: "string",
          description: "Identifier for this stats record, e.g., 'rating_distribution'"
        },
        platforms: {
          bsonType: "object",
          description: "Platform-specific statistics",
          patternProperties: {
            "^[a-zA-Z0-9]+$": {
              bsonType: "object"
            }
          }
        },
        period: {
          bsonType: "string",
          enum: ["all_time", "90_days", "30_days", "7_days"],
          description: "Time period for these stats"
        },
        updated_at: {
          bsonType: "date",
          description: "When this record was last updated"
        }
      }
    }
  }
});

// Create indexes for the platform_stats collection
db.platform_stats.createIndex({ "updated_at": 1 });
db.platform_stats.createIndex({ "_id": 1, "period": 1 }, { unique: true });

// Popular product comparisons cache
db.createCollection("product_comparisons", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["products", "comparison_data", "updated_at"],
      properties: {
        products: {
          bsonType: "array",
          description: "Array of product IDs in this comparison",
          items: {
            bsonType: "objectId"
          }
        },
        hash: {
          bsonType: "string",
          description: "Hash of sorted product IDs for quick lookup"
        },
        comparison_data: {
          bsonType: "object",
          description: "Pre-computed comparison data"
        },
        view_count: {
          bsonType: "int",
          description: "Number of times this comparison has been viewed"
        },
        updated_at: {
          bsonType: "date",
          description: "When this record was last updated"
        },
        expires_at: {
          bsonType: "date",
          description: "When this cache record should expire"
        }
      }
    }
  }
});

// Create indexes for the product_comparisons collection
db.product_comparisons.createIndex({ "hash": 1 }, { unique: true });
db.product_comparisons.createIndex({ "products": 1 });
db.product_comparisons.createIndex({ "view_count": -1 });
db.product_comparisons.createIndex({ "updated_at": 1 });
db.product_comparisons.createIndex({ "expires_at": 1 }, { expireAfterSeconds: 0 }); 