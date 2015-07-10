#include <Python.h>
#include "/usr/share/pyshared/numpy/core/include/numpy/arrayobject.h"
#include <math.h>

#define PARAMVAL_OFFSET  1
#define CLASS_OFFSET     2
#define NEIGHBORS_OFFSET 3

#define TRUE  1
#define FALSE 0

static PyObject *
bestSplit_system(PyObject *self, PyObject *args)
{
  int i;// loop index
  int j;

  int derp = 0;

  int numCells;
  int numNeighbors;

  PyObject *inputParamVals;
  PyArrayObject *py_ParamVals;
  double * c_ParamVals;
  PyObject *inputClasses;
  PyArrayObject *py_Classes;
  int * c_Classes;
  PyObject *inputNeighbors;
  PyArrayObject *py_Neighbors;
  int * c_Neighbors;

  double E; // entropy pre-split
  double E1; //entropy of partition 1
  double E2; //entropy of partition 2
  double Eprime;
  double infoGain;
  double SIG;
  double maxSIG;
  double alpha;

  int n1;//total size of first partition
  int n2;//total size of second partition

  double value;
  double final_value;

  int A_counts[2] = {0,0}; // count of each class in the first partition
  int B_counts[2] = {0,0}; // count of each cleass in the second partition

  double nsar;
  double TotalNSAR;
  double avg_NSAR;

  int oldCountOfHomogenousNeighbors;
  int newCountOfHomogenousNeighbors;
  double bestSplit_out;
  if (!PyArg_ParseTuple(args, "OOOddii", &inputParamVals,&inputClasses,&inputNeighbors,&E,&alpha,&numCells,&numNeighbors))
  {
      return NULL;
  }
  //this will convert sequences to array types if needed
  py_ParamVals = (PyArrayObject *)
             PyArray_ContiguousFromObject(inputParamVals, PyArray_DOUBLE, 1, 1);
  if (py_ParamVals == NULL)
  {
      return NULL;
  }
  py_Classes = (PyArrayObject *)
             PyArray_ContiguousFromObject(inputClasses, PyArray_INT, 1, 1);
  if (py_Classes == NULL)
  {
      return NULL;
  }
  py_Neighbors = (PyArrayObject *)
             PyArray_ContiguousFromObject(inputNeighbors, PyArray_INT, 2, 2);
  if (py_Neighbors == NULL)
  {
      return NULL;
  }

  c_ParamVals = (double *)(py_ParamVals->data);
  c_Classes = (int *)(py_Classes->data);
  c_Neighbors = (int *)(py_Neighbors->data);


  //-------------------------------------------
  //Make C array from python numeric arrays
  //-------------------------------------------

  n1 = numCells;
  n2 = 0;
  int updateList[numCells]; // whenever a pixel is moved from one partition to the other, we need to recalculate its NSAR
  double NSARs[numCells];
  TotalNSAR = 0;
  for (i = 1;i < numCells; i++)
  {
    NSARs[i] = 1;  // If no partition is made, all NSARS are 1, thus the initialization
    A_counts[c_Classes[i]] += 1; //Initialize A_counts (A starts containing all cells)
//    A_counts[0] += 1; //Initialize A_counts (A starts containing all cells)
  }
  final_value = c_ParamVals[numCells-1]; //get feature value of last cell from the sorted list
  value = c_ParamVals[0];
  bestSplit_out = value;
  maxSIG = -1;
                              // outer loop covers all the values of the parameter
  while (value < final_value) // we don't want to partition on the last value, because it doesn't split data
  {
    derp++;
                                                      // inner loop covers the cells of that value
    while (c_ParamVals[n2] <= value) // n2 can also be used as an iterator here, as it increases exactly once each iteration
    {

      updateList[n2] = TRUE;
      A_counts[c_Classes[n2]] -= 1;
      B_counts[c_Classes[n2]] += 1;

      for (i=0; i<numNeighbors;i++)
      {
        if (c_Neighbors[n2*numNeighbors+i] != -1)
        {
          updateList[c_Neighbors[n2*numNeighbors+i]] = TRUE;
        }
      }
      n1 -= 1;
      n2 += 1;
    }
    value = c_ParamVals[n2];
    //information gain calculation
    E1 = 0;
    E2 = 0;
    for (i=0;i<2;i++){
      if (A_counts[i] != 0)
        E1 -= (float)A_counts[i]/(float)n1*log2((float)A_counts[i]/(float)n1);
      if (B_counts[i] != 0)
        E2 -= (float)B_counts[i]/(float)n2*log2((float)B_counts[i]/(float)n2);
    }
    Eprime = (float)n1/(float)(n1+n2)*E1+(float)n2/(float)(n1+n2)*E2;
    infoGain = E-Eprime;
    //NSAR calculation
    for (i=0;i<numCells;i++)
    {
      if (updateList[i])
      {
        oldCountOfHomogenousNeighbors = 0;
        newCountOfHomogenousNeighbors = 0;
        for (j=0;j<numNeighbors;j++) // for each neighbor entry
        {
          if (c_Neighbors[n2*numNeighbors+j] != -1) // if the entry isn't empty
          {
            if (c_Classes[i] == c_Classes[c_Neighbors[i*numNeighbors+j]]) //if cell has same class as neighbor
            {
              oldCountOfHomogenousNeighbors++;
              if ((c_ParamVals[i] <= value)^(c_ParamVals[c_Neighbors[i*numNeighbors+j]]<=value)) // if neighbor is in same partition as pixel
                newCountOfHomogenousNeighbors++;
            }
          }
        }
        if (oldCountOfHomogenousNeighbors == 0)
          nsar = 1;
        else
          nsar = newCountOfHomogenousNeighbors/oldCountOfHomogenousNeighbors;
        TotalNSAR = TotalNSAR - NSARs[i] + nsar;
        NSARs[i] = nsar;
        updateList[i] = FALSE;
      }
    }
    avg_NSAR = TotalNSAR/numCells;
    SIG = (1-alpha)*infoGain + alpha*avg_NSAR; // weighted sum of IG and avg_NSAR
    if (SIG >= maxSIG)
    {
      maxSIG = SIG;
      bestSplit_out = value;
    }
  }
  //  PyArrayObject *return_array = (PyArrayObject *) PyArray_FromDimsAndData(2,dims,PyArray_INT, (char*) c_array);
  return Py_BuildValue("dd", bestSplit_out,maxSIG);

}

static PyMethodDef BestSplitMethods[] = {
    {"findSplit",  bestSplit_system, METH_VARARGS,
     "finds the best split according to the SIG algorithm"},
    {NULL, NULL, 0, NULL}        /* Sentinel */
};

PyMODINIT_FUNC
initbestSplit(void)
{
    (void) Py_InitModule("bestSplit", BestSplitMethods);
    import_array();
}

