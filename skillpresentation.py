"""The character window has three columns for five actual skill grades."""


def CompactGrade(grade):
    return 0 if grade <= 0 else 1 if grade <= 2 else 2


def ColumnGrades(actualGrade):
    return (0, 2 if actualGrade >= 2 else 1, max(3, actualGrade))
