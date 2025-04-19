# Analyzer 
## Project description
This project or better say program aims to use technical chart analysis paired with fundamental analysis and the tools 
of descriptive statistics to make predictions about the development of certain values, companies or indices on the 
financial market. This project also aims to provide added value by adding functionality to my own financial accounting. 
This will allow me to keep track of my own personal income and expenses. Because before you can even imagine how 
wonderful it would be to be financially prosperous and free, you first have to get your costs under control.

![Status](https://img.shields.io/badge/Status-In%20Development-yellow)
## Useful Features

### KMeans-Volatility-Cluster Indicator
![DAX-KMeans.png](docs/pics/DAX-KMeans.png)

**What's that?**

> What you see here is by my self implemented AI KMeans-Clustering-Algorithm. It falls under the category of unsupervised
> machine learning algorithms. I use this algorithm to first visually examine the volatility of various stock indices.
> The picture show you daily percentage change in the closing price from the dax over the last 20 years.
> 
> Where the volatility of the percentage change is particularly high, the price also falls during this period. Regardless 
> of whether there were percentage changes upwards or downwards. However, it is usually the first downward outliers that 
> reveal a bearish phase. In all other cases, the price always rises steeply.
>
> The algorithm works by iteratively assigning data points to clusters based on their proximity to a central point, and 
> then recalculating that central point to better represent the assigned data.

If you’re thirsty for more technical details how the algorithm work, I recommend diving into 
[Victor Lavrenko’s video series](https://www.youtube.com/watch?v=_aWzGGNrcic&list=PLIKsw1YCzYKPYvPtUbrcsDT5Y2ILcRm1D&index=29). 
As an excellent data science teacher, he provides valuable insights and knowledge. 


### Pivot Level-Chart

![example-pivots.png](docs/pics/example-pivots.png)

**Again, what's that?**

> A working implementation of an algorithm for determining the 
> [pivot](https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-overlays/pivot-points) 
> levels on a chart. And also the probability to reach this levels during the actual month on the right side of the legend 
> based on historical data.

### Planed Features

#### KMeans and Hidden Markov Model united
My next vision is to use the [Hidden Markov Model](https://en.wikipedia.org/wiki/Hidden_Markov_model) combined with my
KMeans-Volatility-Cluster indicator like in that picture shown:

![Kmeans-HMM-united.png](docs/pics/Kmeans-HMM-united.png)

The special thing about the Hidden Markov Model is that it can predict the weather. I want to use it to predict the 
weather on the stock market. With the pre-process of assigning data points to clusters based on the 
KMeans-Volatility-Cluster indicator...

**Explanation**
> You have some kind of **

I use the [gics](https://en.wikipedia.org/wiki/Global_Industry_Classification_Standard) standard for this.

## Build With
- Python
	- pandas
	- seaborn
    - plotly
	- mysql-connector-python
    - SQLAlchemy
	- plotly
    - Sphinx
    - jupyter notebook

## Important developments
As part of the project, I developed a rudimentary ERM mapper, or more accurately, a database driver. I was looking for 
a way to abstract the complexity of database queries in the code but at the same time keep it flexible enough for my 
needs. Here you can see the SqliteDatamanager class, which only contains two methods, select and query. The select 
method only has read access to the database and query also has write access. Use it and be happy with sqlite :slightly_smiling_face:

```python
import mysql.connector
import logging
from time import sleep


logger = logging.getLogger(__name__)
logging.basicConfig(filename="datalayer.log", encoding="utf-8", level=logging.ERROR,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d, %H:%M:%S')

class MysqlConnectorManager:

    def __init__(self, config: dict):

        self.config = config

    def init_conn(self, attempts=3, delay=2):

        """
        Initialize the connection with my mariadb database.

        :param attempts: amount of attempts
        :param delay: waiting seconds for trying to reconnect
        """

        attempt = 1
        # Implement a reconnection routine
        while attempt < attempts + 1:
            try:
                return mysql.connector.connect(**self.config)
            except (mysql.connector.Error, IOError) as err:
                if attempts is attempt:
                    # Attempts to reconnect failed; returning None
                    logger.info("Failed to connect, exiting without a connection: %s", err)
                    return None
                logger.error(
                    "Connection failed: %s. Retrying (%d/%d)...",
                    err,
                    attempt,
                    attempts - 1,
                )
                # progressive reconnect delay
                sleep(delay ** attempt)
                attempt += 1
        return None

    def select(self, sqlstring):

        mydb = self.init_conn()
        cursor = mydb.cursor()

        try:
            cursor.execute(sqlstring)
        except (mysql.connector.Error, IOError) as err:
            raise err

        result = cursor.fetchall()
        mydb.close()
        return result

    def query(self, sqlstring, val=None) -> int:

        mydb = self.init_conn()
        mycursor = mydb.cursor()

        try:
            if isinstance(val, list):
                mycursor.executemany(sqlstring, val)
            elif isinstance(val, tuple):
                mycursor.execute(sqlstring, val)
            elif not val:
                mycursor.execute(sqlstring)

        except (mysql.connector.Error, IOError) as err:
            raise err

        mydb.commit()
        mydb.close()
        return mycursor.rowcount

```