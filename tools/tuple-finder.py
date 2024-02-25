#check everywhere for unhandled tuples

import ast
import os


class TupleUnpackingVisitor(ast.NodeVisitor):

  def visit_Assign(self, node):
    if isinstance(node.targets[0], ast.Tuple):
      # Count of variables on the left side of assignment
      left_side_count = len(node.targets[0].elts)

      # Handling the right side based on its type
      if isinstance(node.value, ast.Tuple):
        right_side_count = len(node.value.elts)
      elif isinstance(node.value, ast.List):
        right_side_count = len(node.value.elts)
      elif isinstance(node.value, ast.Call):
        # If it's a function call, we can't determine the exact number
        # of values, so we skip this check
        return
      else:
        # Log unhandled types
        print(
            f"Unhandled right-side type in file {self.filename} at line {node.lineno}. Please review manually."
        )
        return

      # Compare left and right side counts
      if left_side_count != right_side_count:
        print(
            f"Unbalanced tuple unpacking found in file {self.filename} at line {node.lineno}. "
            f"Expected {left_side_count} values, found {right_side_count} values."
        )

  def visit_For(self, node):
    # Check for tuple unpacking in for loops
    if isinstance(node.target, ast.Tuple):
      loop_var_count = len(node.target.elts)

      # Check for starred expression in unpacking
      for elt in node.target.elts:
        if isinstance(elt, ast.Starred):
          print(
              f"Starred expression found in for-loop unpacking in file {self.filename} at line {node.lineno}. This might be a potential source of error."
          )
          return

      # If we're iterating over a list of tuples, we can compare sizes
      if isinstance(node.iter, (ast.List, ast.Tuple)):
        if all(
            isinstance(elt, (ast.Tuple, ast.List)) for elt in node.iter.elts):
          iter_tuple_size = len(node.iter.elts[0].elts)
          if loop_var_count != iter_tuple_size:
            print(
                f"Unbalanced tuple unpacking in for-loop found in file {self.filename} at line {node.lineno}. "
                f"Expected {loop_var_count} values in loop variables, but found tuples of size {iter_tuple_size} in iterable."
            )

  def check_file(self, filename):
    self.filename = filename
    with open(filename, 'r') as f:
      tree = ast.parse(f.read())
      self.visit(tree)


def identify_tuple_unpacking_in_specified_directories(directories):
  visitor = TupleUnpackingVisitor()
  for directory in directories:
    for filename in os.listdir(directory):
      if filename.endswith('.py'):
        full_path = os.path.join(directory, filename)
        visitor.check_file(full_path)


# Specify the directories to check. These are relative to ./tools directory:
directories_to_check = ['.', '..', '../agents']
identify_tuple_unpacking_in_specified_directories(directories_to_check)
