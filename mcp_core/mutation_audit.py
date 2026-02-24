
import logging


def audit_mutation_score(
    task_id: str, 
    score: float, 
    threshold: float = 80.0
) -> bool:
    """
    Log the mutation score and determine if it passes the Quality Gate.
    """
    logging.info(
        f"AUDIT [Task {task_id}]: Mutation Score = {score}% (Threshold: {threshold}%)")

    if score < threshold:
        logging.warning(f"❌ Task {task_id} FAILED mutation gate.")
        return False

    logging.info(f"✅ Task {task_id} PASSED mutation gate.")
    return True
