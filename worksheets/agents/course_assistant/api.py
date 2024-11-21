import datetime
from uuid import UUID, uuid4

import cvc5
from cvc5 import Kind


def submit_student_form(
    student_name,
    advisor_name,
    student_id,
    student_email_address,
    proposed_date_for_degree_conferral,
    is_coterm_student,
    foundation_couses_details,
    **kwargs,
):
    return {
        "status": "success",
        "params": {
            "student_name": student_name,
            "advisor_name": advisor_name,
            "student_id": student_id,
            "student_email_address": student_email_address,
            "proposed_date_for_degree_conferral": proposed_date_for_degree_conferral,
            "is_coterm_student": is_coterm_student,
            "foundation_couses_details": foundation_couses_details,
        },
        "response": {
            "transaction_id": uuid4(),
            "transaction_date": datetime.date.today(),
            "transaction_time": datetime.datetime.now().time(),
        },
    }


def foundation_courses_taken_meet_reqs(
    taken_logic_automata_complexity,
    logic_course,
    logic_course_units_taken,
    taken_probability,
    probablity_course,
    probability_course_units_taken,
    taken_algorithmic_analysis,
    algorithmic_analysis_course,
    algorithmic_analysis_course_units_taken,
    taken_computer_organisation,
    computer_organisation,
    computer_organisation_course_units_taken,
    taken_principles_of_computer_systems,
    principles_of_computer_system,
    principles_of_computer_system_course_units_taken,
    **kwargs,
):
    course_mapping = {
        "ms&e220": "msande220",
    }

    course_choices = {}
    for val in probablity_course.slottype.__members__.values():
        course_choices[val.name.replace(" ", "").lower()] = [False, 3]
    for val in logic_course.slottype.__members__.values():
        course_choices[val.name.replace(" ", "").lower()] = [False, 3]
    for val in algorithmic_analysis_course.slottype.__members__.values():
        course_choices[val.name.replace(" ", "").lower()] = [False, 3]
    for val in computer_organisation.slottype.__members__.values():
        course_choices[val.name.replace(" ", "").lower()] = [False, 3]
    for val in principles_of_computer_system.slottype.__members__.values():
        course_choices[val.name.replace(" ", "").lower()] = [False, 3]

    if taken_logic_automata_complexity:
        course_choices[logic_course.value.replace(" ", "").lower()] = [
            True,
            logic_course_units_taken.value,
        ]
    if taken_probability:
        course_choices[probablity_course.value.replace(" ", "").lower()] = [
            True,
            probability_course_units_taken.value,
        ]
    if taken_algorithmic_analysis:
        course_choices[algorithmic_analysis_course.value.replace(" ", "").lower()] = [
            True,
            algorithmic_analysis_course_units_taken.value,
        ]
    if taken_computer_organisation:
        course_choices[computer_organisation.value.replace(" ", "").lower()] = [
            True,
            computer_organisation_course_units_taken.value,
        ]
    if taken_principles_of_computer_systems:
        course_choices[principles_of_computer_system.value.replace(" ", "").lower()] = [
            True,
            principles_of_computer_system_course_units_taken.value,
        ]

    for key, val in course_mapping.items():
        if course_choices.get(key):
            course_choices[val] = course_choices.pop(key)

    res, explanation = check_cs_master_requirements(course_choices)
    return {
        "foundation_courses_meet_reqs": res,
        "explanation": explanation,
    }


def check_cs_master_requirements(course_choices):
    # Initialize solver
    solver = cvc5.Solver()
    solver.setOption("produce-unsat-cores", "true")
    solver.setOption("produce-models", "true")
    solver.setLogic("ALL")

    # Define course variables

    # Logic courses
    cs103 = solver.mkConst(solver.getBooleanSort(), "CS103")
    cs103_units = solver.mkConst(solver.getIntegerSort(), "CS103_units")

    # Algorithmic Analysis courses
    cs161 = solver.mkConst(solver.getBooleanSort(), "CS161")
    cs161_units = solver.mkConst(solver.getIntegerSort(), "CS161_units")

    # Computer Organization courses
    cs107 = solver.mkConst(solver.getBooleanSort(), "CS107")
    cs107e = solver.mkConst(solver.getBooleanSort(), "CS107E")

    cs107_units = solver.mkConst(solver.getIntegerSort(), "CS107_units")
    cs107e_units = solver.mkConst(solver.getIntegerSort(), "CS107E_units")

    # Principles of Computer Systems courses
    cs110 = solver.mkConst(solver.getBooleanSort(), "CS110")
    cs111 = solver.mkConst(solver.getBooleanSort(), "CS111")

    cs110_units = solver.mkConst(solver.getIntegerSort(), "CS110_units")
    cs111_units = solver.mkConst(solver.getIntegerSort(), "CS111_units")

    # Probability courses
    cs109 = solver.mkConst(solver.getBooleanSort(), "CS109")
    ee178 = solver.mkConst(solver.getBooleanSort(), "EE178")
    stat116 = solver.mkConst(solver.getBooleanSort(), "Stat116")
    cme106 = solver.mkConst(solver.getBooleanSort(), "CME106")
    msande220 = solver.mkConst(solver.getBooleanSort(), "MSandE220")

    cs109_units = solver.mkConst(solver.getIntegerSort(), "CS109_units")
    ee178_units = solver.mkConst(solver.getIntegerSort(), "EE178_units")
    stat116_units = solver.mkConst(solver.getIntegerSort(), "Stat116_units")
    cme106_units = solver.mkConst(solver.getIntegerSort(), "CME106_units")
    msande220_units = solver.mkConst(solver.getIntegerSort(), "MSandE220_units")

    # Course requirements
    # At least one course from each group must be true
    course_requirements = [
        cs103,
        cs161,
        (cs107, cs107e),
        (cs110, cs111),
        (cs109, ee178, stat116, cme106, msande220),
    ]
    for requirement in course_requirements:
        if isinstance(requirement, tuple):
            solver.assertFormula(solver.mkTerm(Kind.OR, *requirement))
        else:
            solver.assertFormula(
                solver.mkTerm(Kind.EQUAL, requirement, solver.mkTrue())
            )

    # all the units must be greater than or equal to 3
    course_units = [
        cs103_units,
        cs161_units,
        cs107_units,
        cs107e_units,
        cs110_units,
        cs111_units,
        cs109_units,
        ee178_units,
        stat116_units,
        cme106_units,
        msande220_units,
    ]
    for unit in course_units:
        solver.assertFormula(
            solver.mkTerm(
                Kind.GEQ,
                unit,
                solver.mkInteger(3),
            )
        )

    # Check satisfiability
    result = solver.checkSat()
    if result.isSat():
        print("The model is satisfiable.")
    else:
        print("The model is unsatisfiable.")

    solver.push()
    # Add the course choices
    for course, (taken, units) in course_choices.items():
        if taken:
            solver.assertFormula(
                solver.mkTerm(Kind.EQUAL, locals()[course.lower()], solver.mkTrue())
            )
            solver.assertFormula(
                solver.mkTerm(
                    Kind.EQUAL,
                    locals()[f"{course.lower()}_units"],
                    solver.mkInteger(units),
                )
            )
        else:
            solver.assertFormula(
                solver.mkTerm(Kind.EQUAL, locals()[course.lower()], solver.mkFalse())
            )
            solver.assertFormula(
                solver.mkTerm(
                    Kind.EQUAL,
                    locals()[f"{course.lower()}_units"],
                    solver.mkInteger(0),
                )
            )

    result = solver.checkSat()
    if result.isSat():
        return True, None
    else:
        core = solver.getUnsatCore()
        print("Unsat core is: ", core)
        return False, str(core)
