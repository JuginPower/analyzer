# Implementation of the KMeans-Clustering-Algorithm

Like in the [classes.py](../classes.py) you see the code of *KMeansClusterMain* at line 117.
This part bellow in particular is the heart of the entire implementation.

#### Like in the video from [Victor Lavrenko](https://www.youtube.com/watch?v=_aWzGGNrcic) we do...

```python
from copy import copy

def fit(self, datapoints: list):

    """
    Begins the process where the reassignment of the centroids continued till the assignment of the clusters for
    each datapoint ends

    :param datapoints: one dimensional list of numerical datapoints
    """

    centroids = self._place_centroids(datapoints)
    ordered_clusters = self._assign_nearest_centroid(datapoints, centroids)
    new_centroids = self._replace_centroids(datapoints, ordered_clusters, centroids)
    new_ordered_clusters = self._assign_nearest_centroid(datapoints, new_centroids)

    while ordered_clusters != new_ordered_clusters:

        # Necessary because of call by object behaviour from python its safely make independent copies and reassign
        ordered_clusters = copy(new_ordered_clusters)
        centroids = copy(new_centroids)

        new_centroids = self._replace_centroids(datapoints, ordered_clusters, centroids)
        new_ordered_clusters = self._assign_nearest_centroid(datapoints, new_centroids)

    self.labels = new_ordered_clusters
    self.centroids = centroids
```

1. Take a set of data points; the order doesn't matter, as long as the data points are numerical values in `datapoints: list`.

```python
def _place_centroids(self, datapoints: list) -> dict:

    """
    Choose random centroids in the list

    :param datapoints: A list with numerical values

    :return dict: A dictionary with the centroids
    """

    result = {}

    for n in range(self.clusters):
        centroid = random.choice(datapoints)
        result.update({n: centroid})

    return result
```

2. Choose centroids at random locations in space. They can also be randomly chosen data points within the given 
set. I use here the standard random library from python.

```python
def _assign_nearest_centroid(self, datapoints: list, centroids: dict) -> list:

    """
    Find the nearest centroid for any datapoint and assign this datapoint to this centroid

    :param datapoints: A list wich is assumed to be the whole dataset.
    :param centroids: A dictionary with the given centroids.

    :return list: An ordered list with the choosen centroids.
    """

    ordered_centroids = []

    for dp in datapoints:

        distances = []
        names = []

        for cent in centroids.items():
            distances.append(abs(dp - cent[1]))
            names.append(cent[0])

        index_min_distance = distances.index(min(distances))
        ordered_centroids.append(names[index_min_distance])

    return ordered_centroids
```

3. Next, find the nearest centroid to each data point. Normally, the Euclidean distance is taken in...  

> two-dimensional space:

$$d(P_1, P_2) = \sqrt{(x_2 - x_1)^2 + (y_2 - y_1)^2}$$ 

> three-dimensional space:

$$d(P_1, P_2) = \sqrt{(x_2 - x_1)^2 + (y_2 - y_1)^2 + (z_2 - z_1)^2}$$

But here I'm simply using the magnitude of the difference between two data points as the distance in a one-dimensional 
space: `distances.append(abs(dp - cent[1]))`. It could later be expanded for other use cases if needed.


