from typing import List, Tuple

class Function:
    def __init__(self, name: str, services):
        """
        :param name: function name
        :param services: Can be a string or a list. If it is a string, it should be formed as "AWS S3, AWS ECR, AWS IAM, AWS API Gateway, AWS CloudWatch"
        """
        self.name = name
        self.services = services

    def __repr__(self):
        return f"{self.name}({self.services})"

def jaccard_distance(set1: set, set2: set) -> float:
    """
    Calculate the Jaccard distance between two sets
    If the request (set1) set is empty, return 0 (assuming no requirement conflicts with any candidate);
    If the candidate set (set2) is empty, return 1 (completely mismatched);
    Otherwise, return 1- (intersection size/union size).
    """
    if set1 == {"None"}:
        return 0.0
    if set2 == {"None"} and set1 != {"None"}:
        return 1.0

    union = set1 | set2
    if not union:
         return 1.0
    return 1 - len(set1 & set2) / len(union)

def coverage(set1: set, set2: set) -> float:
    """
    Calculate the coverage of the candidate set on the request set:
    If the request set is empty, return 1.0;
    If the candidate set is empty, return 0.0;
    Otherwise, return (intersection size/total number of elements in the request).
    """
    if not set1 or set1 == {"None"}:
        return 1.0
    if (not set2 or set2 == {"None"}) and set1 != {"None"}:
        return 0.0
    return len(set1 & set2) / len(set1)

def is_dominated(p1: Tuple[float, float], p2: Tuple[float, float]) -> bool:
    """
    Determine whether p1 is dominated by p2: p1 has a larger Jaccard distance and smaller coverage (at least one of which is strict)
    """
    return p1[0] >= p2[0] and p1[1] <= p2[1] and (p1[0] > p2[0] or p1[1] < p2[1])

def pareto_single_function_selection(request_services: str, candidate_functions: List[Function]):
    # Processing request services as a collection
    if isinstance(request_services, str):
        request_services_set = {s.strip() for s in request_services.split(",") if s.strip()}
    elif isinstance(request_services, list):
        request_services_set = {s.strip() for s in request_services}
    else:
        request_services_set = set()

    single_match = []   # Used to save matching items that are "single element and equal"
    evaluated = []      # The remaining items that require Pareto to to be done later

    for f in candidate_functions:
        
        if isinstance(f.services, str):
            services_list = [s.strip() for s in f.services.split(",") if s.strip()]
        elif isinstance(f.services, list):
            services_list = [s.strip() for s in f.services]
        else:
            services_list = []
        candidate_set = set(services_list) if services_list else {"None"}

        if len(request_services_set) == 1 and len(candidate_set) == 1:
            # Both only contain one element
            if request_services_set == {"None"} or request_services_set == candidate_set:
                single_match.append((f, 0.0, 1.0)) 
            elif candidate_set == {"None"} and request_services_set != {"None"}:
                continue
            continue

        jd = jaccard_distance(request_services_set, candidate_set)
        cov = coverage(request_services_set, candidate_set)
        evaluated.append((f, jd, cov))

    best = []
    suboptimal = []
    for f, jd, cov in evaluated:
        if cov == 0.0:
            continue
        if cov == 1.0:
            best.append((f, jd, cov))
        else:
            suboptimal.append((f, jd, cov))

    selected = single_match + best.copy()  # First, add the strictly matched single element, and then add the original best
    pareto_front = []
    for i, (fi, jdi, covi) in enumerate(suboptimal):
        dominated = False
        for j, (fj, jdj, covj) in enumerate(suboptimal):
            if i != j and is_dominated((jdi, covi), (jdj, covj)):
                dominated = True
                break
        if not dominated:
            pareto_front.append((fi, jdi, covi))

    selected += pareto_front

    return selected
