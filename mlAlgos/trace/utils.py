"""
Some utility functions I need in several classes
"""
import constants

def gen_one_hot_encoding_col_names() -> list[str]:
          a=  [f"S_{ind}" for ind in range(len(constants.SERVICES))]
          return a


"""builds the column names for all the response variables"""
def build_colum_names_for_adf_mat_df() -> list[str]:
     result = []
     for _ , out_val in constants.SERVICES.items():
          for _ , in_val in constants.SERVICES.items():
               result.append(f"{out_val}_{in_val}")

     #print(result)
     return result