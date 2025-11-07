Implementation of KMeans-Algorithm
##################################

What you see here is my own implemented version of the AI ​​K-means clustering algorithm. It falls into the
category of unsupervised machine learning algorithms. K-means clustering is a popular machine learning technique.
Essentially, this algorithm automatically groups data points that are close to each other.

`Victor Lavrenko <https://www.youtube.com/@vlavrenko>`__ has created a complete video series on clustering algorithms.

.. image:: https://img.youtube.com/vi/_aWzGGNrcic/0.jpg
   :alt: Victor Lavrenko's video series
   :target: https://www.youtube.com/watch?v=_aWzGGNrcic
   :width: 480px

.. Need here to open a new page youtube


I primarily used this video series to help me implement the following KMeans algorithm.

How it works
============

It's not complicated, you just need to know the most basic arithmetic operations. It begins with placing centroids on
random locations let them call :math:`x_1 \ldots x_n`. These centroids also determine the number of groupings or
clusters to which the data points are later assigned.

The question that naturally arises here is: how do we know how many clusters we need? Because I already assumed that as
an argument when implementing the algorithm.