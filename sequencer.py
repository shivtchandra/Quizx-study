# sequencer.py

from typing import Union # <--- ADD THIS IMPORT

class AdaptiveSequencer:
    """Decides which skill to present to the student next."""
    def __init__(self, knowledge_graph, bkt_model, mastery_threshold=0.95):
        self.graph = knowledge_graph
        self.bkt = bkt_model
        self.mastery_threshold = mastery_threshold
        
        # Initialize student's knowledge state.
        # Start with the initial probability from the BKT model for all skills.
        self.student_knowledge = {
            skill_id: self.bkt.p_init for skill_id in self.graph
        }

    # vvvv THIS IS THE LINE WE'RE FIXING vvvv
    def get_next_skill(self) -> Union[str, None]:
        """
        Finds the next appropriate skill for the student to work on.
        A skill is appropriate if its prerequisites are met but it is not yet mastered.
        """
        for skill_id, skill_info in self.graph.items():
            # Check if this skill is already mastered
            if self.student_knowledge[skill_id] >= self.mastery_threshold:
                continue

            # Check if all prerequisites for this skill are met
            prereqs_met = True
            for prereq_id in skill_info['prerequisites']:
                if self.student_knowledge[prereq_id] < self.mastery_threshold:
                    prereqs_met = False
                    break
            
            if prereqs_met:
                return skill_id # Found a skill that's ready to be learned

        return None # No new skills available, user has mastered everything!

    def update_student_knowledge(self, skill_id, is_correct):
        """Updates the BKT model with the student's answer."""
        p_mastery_prev = self.student_knowledge[skill_id]
        p_mastery_new = self.bkt.update_skill_mastery(p_mastery_prev, is_correct)
        self.student_knowledge[skill_id] = p_mastery_new