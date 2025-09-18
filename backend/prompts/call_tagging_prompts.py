"""
Call Tagging Prompts - Centralized prompt management for call categorization
"""

class CallTaggingPrompts:
    """Collection of prompts for call tagging service"""
    
    TAGGING_PROMPT = """
Analyze this dental office call and choose ONE category from the predefined list.

PATIENT: {patient_text}
STAFF: {staff_text}

PREDEFINED CATEGORIES (choose ONLY from these):
1. new_patient - First-time patients or people looking for a new dentist
2. emergency - Urgent dental issues, pain, broken teeth, swelling
3. insurance - Insurance verification, coverage questions, benefit inquiries
4. appointment_booking - Scheduling new appointments
5. appointment_confirm - Confirming existing appointments
6. appointment_cancel - Canceling or rescheduling appointments
7. general_inquiry - General questions about hours, location, services, pricing
8. cleaning - Routine cleanings, checkups, preventive care
9. cosmetic - Whitening, braces, veneers, smile makeovers
10. major_treatment - Implants, crowns, root canals, oral surgery
11. billing - Payment questions, billing issues, account inquiries

Choose the BEST MATCH from these 11 categories. If none fit perfectly, choose "general_inquiry".

Respond with ONLY the category name (e.g., "emergency" or "billing").

Category:"""