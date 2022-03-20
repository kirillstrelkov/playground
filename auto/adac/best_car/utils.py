COLUMN_FEATURE = "features"
COLUMN_FEATURE_TYPE = "type"
COLUMN_FEATURE_WEIGHT = "weight"
COLUMN_FEATURE_RANGE = "range"


class FeatureType(object):
    MORE_IS_BETTER = "more is better"
    LESS_IS_BETTER = "less is better"
    CATEGORY = "category"
    SKIP = "skip"

    @classmethod
    def all(cls):
        return {cls.MORE_IS_BETTER, cls.LESS_IS_BETTER, cls.SKIP, cls.CATEGORY}
