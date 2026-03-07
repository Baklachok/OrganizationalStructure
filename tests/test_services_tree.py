from app.schemas.department import DepartmentCreate
from app.schemas.employee import EmployeeCreate
from app.services.departments import create_department, get_department_tree
from app.services.employees import create_employee
from sqlalchemy.orm import Session


def test_get_department_tree_respects_depth_and_include_employees(db_session: Session) -> None:
    root = create_department(db_session, DepartmentCreate(name="Root"))
    child = create_department(db_session, DepartmentCreate(name="Child", parent_id=root.id))
    create_department(db_session, DepartmentCreate(name="Grandchild", parent_id=child.id))

    create_employee(db_session, root.id, EmployeeCreate(full_name="A One", position="Lead"))
    create_employee(db_session, child.id, EmployeeCreate(full_name="B Two", position="Dev"))

    tree_depth_1 = get_department_tree(
        db_session,
        root.id,
        depth=1,
        include_employees=True,
    )
    assert tree_depth_1["department"]["id"] == root.id
    assert len(tree_depth_1["children"]) == 1
    assert tree_depth_1["children"][0]["children"] == []
    assert len(tree_depth_1["employees"]) == 1

    tree_depth_2_without_employees = get_department_tree(
        db_session,
        root.id,
        depth=2,
        include_employees=False,
    )
    assert len(tree_depth_2_without_employees["children"][0]["children"]) == 1
    assert tree_depth_2_without_employees["employees"] == []
    assert tree_depth_2_without_employees["children"][0]["employees"] == []
