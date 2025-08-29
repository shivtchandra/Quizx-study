# bkt.py

class BKT:
    """A simple Bayesian Knowledge Tracing model."""
    def __init__(self, p_init=0.0, p_transit=0.2, p_slip=0.1, p_guess=0.2):
        self.p_init = p_init      # Probability of knowing the skill beforehand
        self.p_transit = p_transit  # Probability of learning the skill after practice
        self.p_slip = p_slip      # Probability of making a mistake when you know the skill
        self.p_guess = p_guess    # Probability of guessing correctly when you don't know

    def update_skill_mastery(self, p_mastery_prev, is_correct):
        """
        Updates the probability of skill mastery based on a single answer.
        """
        p_slip = self.p_slip
        p_guess = self.p_guess

        if is_correct:
            # The student answered correctly.
            # This could be because they know the skill and didn't slip,
            # OR they don't know it but guessed correctly.
            p_correct_given_mastery = p_mastery_prev * (1 - p_slip)
            p_correct_given_no_mastery = (1 - p_mastery_prev) * p_guess
            
            p_mastery_current = p_correct_given_mastery / (p_correct_given_mastery + p_correct_given_no_mastery)
        else:
            # The student answered incorrectly.
            # This could be because they know the skill but slipped,
            # OR they don't know it and didn't guess correctly.
            p_incorrect_given_mastery = p_mastery_prev * p_slip
            p_incorrect_given_no_mastery = (1 - p_mastery_prev) * (1 - p_guess)

            p_mastery_current = p_incorrect_given_mastery / (p_incorrect_given_mastery + p_incorrect_given_no_mastery)

        # After the observation, account for the chance they learned from it.
        p_mastery_final = p_mastery_current + (1 - p_mastery_current) * self.p_transit
        
        return p_mastery_final