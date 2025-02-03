# Machine Learning Algorithms for Distributed Tracing Data

This is just for developing and keeping track of decisions we make throughout the process

# Constructing Experiments for the ML Data based in distributed tracing

     One of the questions that hunt me is how much data do we actually need?
     We inject faults into the recommendationservice for example -> do we need to collect data from all microservices in the SUE?

     I tried collecting dis. Traces from all Microservices these were the responses from Jaeger:

          [2024-11-27 14:17:25,161] DESKTOP-BP9O4AV/INFO/oxn.observer: failed to capture accountingservice_traces, proceeding. Cannot concatenate dataframes: Jaeger sent an empty response
          [2024-11-27 14:17:25,226] DESKTOP-BP9O4AV/INFO/oxn.observer: failed to capture adservice_traces, proceeding. Cannot concatenate dataframes: Jaeger sent an empty response
          [2024-11-27 14:17:25,271] DESKTOP-BP9O4AV/INFO/oxn.observer: failed to capture checkoutservice_traces, proceeding. Cannot concatenate dataframes: Jaeger sent an empty response
          [2024-11-27 14:17:25,299] DESKTOP-BP9O4AV/INFO/oxn.observer: failed to capture currencyservice_traces, proceeding. Cannot concatenate dataframes: Jaeger sent an empty response
          [2024-11-27 14:17:25,413] DESKTOP-BP9O4AV/INFO/oxn.observer: failed to capture emailservice_traces, proceeding. Cannot concatenate dataframes: Jaeger sent an empty response
          [2024-11-27 14:17:25,472] DESKTOP-BP9O4AV/INFO/oxn.observer: failed to capture frauddetectionservice_traces, proceeding. Cannot concatenate dataframes: Jaeger sent an empty response
          [2024-11-27 14:17:25,536] DESKTOP-BP9O4AV/INFO/oxn.observer: failed to capture paymentservice_traces, proceeding. Cannot concatenate dataframes: Jaeger sent an empty response

     
     Microservices I got data from:
          - frontend
          - frontend-proxy
          - recommendationservice
          - cartservice
     
     For right now these are the the microservices that are also provoked from Locust.... andd the tasks defined in the experiment.

     ==> we need to define very good experiments for the distributed tracing Algorithm and especially locust tasks.

# Data Mining Method 1: Adjency Matrix

     Some service call themselves "recursively" like cartservice. This is a single trace sorted ascending after invacation time.

               service_name span_kind  ref_type_span_ID  duration
     378  frontend-proxy    server               NaN  355311.0
     377  frontend-proxy    client  536d357fb4be5346  355082.0
     381        frontend    server  3c7d0ba472fe68f1  206676.0
     379        frontend    client  24f53e0ccf93136d  120930.0
     382     cartservice    server  0efa07cb43785b04   23861.0
     385     cartservice    client  1d497080248a57dd    9120.0
     386     cartservice    client  1d497080248a57dd    2198.0
     387     cartservice    client  1d497080248a57dd    1863.0
     380        frontend    client  24f53e0ccf93136d   84384.0
     383     cartservice    server  4b332aa05d7156da    3488.0
     384     cartservice    client  0fb390245f1df848    1623.0

     This can happen because cart_service has redis_cache in the "backend", looking into the source code helps lol.


     Load generation starts outside the frontend proxy for the open-telemetry demo


# Artificial Labeling, supervised Learning and "KPIS" (3.01.2025)

I just found out that in the Paper they label the data "artificially" meaning that they build there labels themselves. They label faults based on on extremes on a confidence interval they build themsevles around the average estimation.

So eventually they have two steps of inaccuracies. We do have natural labeling provided by OXN itself.

However, this gives us the opporunity to build interesting KPIs around the Classification itself. 

1. The ration of how many faulty traces have gRPC errors or how many good traces have gRPC errors.

2. How much does the distribution differ from each other in a response variable between good and fault traces?

'''
     This function is creating the lower and upper bound for the performance anomaly detection per service tuple
     based on very simple "outlier detection". This could be up for discussion for improvements. For now I would leave it this way as stated in the paper.
     Here we use int as a val corresponding to the index in the flattened dataframe
     dict[m_n, [number of observations between MS m and n , average, variance ]]
     at another point in time we pool the variances with the assuption that the datasets are independent
 
     def get_bounds_for_service_calls(self) -> dict[str , float]:
          merged = [var.adf_matrices for var in self.variables]
          result = pd.concat(merged, axis=0, ignore_index=True)
          columns_for_average = self.column_names
          average_series = result[columns_for_average].mean()
          series_dict = average_series.to_dict()
          print(series_dict)
          self.weights_of_edges = series_dict

     '''


# Model Evaluation and Metrics

     "Root cause Analysis" is a multi-class classification. When the model is given a trace it should output the class (in this case the microservice) in which (the model) thinks the fault has happened or no Fault would be another class [so eventaully we have Microservices we trained the model on +1 class for the]. To evaluate the model we will calculate a confusion matrix. Which is just a n x n matrix [n corresponds to the number of classes / microseervices].
     This is a good Introduction for confusion matrix: https://towardsai.net/p/l/multi-class-model-evaluation-with-confusion-matrix-and-classification-report


          Right now I am evaluating if I can use Libaries such aus skLearn or PyTorch for the Eval. Or if we need more freedom and should write it out ourselves. 

          >>> input = torch.tensor([0, 0, 1, 1, 1, 2, 1, 2])
          >>> target = torch.tensor([2, 0, 2, 0, 1, 2, 1, 0])
          >>> multiclass_confusion_matrix(input, target, 3)
          tensor([[1, 1, 1],
                    [0, 2, 0],
                    [1, 1, 1]])
     
          This is how multiclass classification is done in pytorch. I ma choossing to store the partly confusion matrix within each traceresposse variable. 

          A good visual representations is given in the paper: https://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber=9711932


     For each variable I want to calculate the following metrics with micro averaging:

          Precision,
          Recall,
          F1 Score,
          the Microservice that was predicted wrong the most of the time,


          Precision and recall curve * for each response variable

          showing the conditional Probability for each variable if it has an error


     A nice Overview of the metrics can be founf in the following paper: ttps://arxiv.org/abs/2008.05756

     ==> how do I do aggreate over all metrics in a meaningful way?

# The Multilayer Perceptron

     The MLP will have 5 layers:
     -  1 Input layer [Dimensions will be the crossproduct of all n^2 + 1 (+ 1 because having no fault is basically the another "microservice" , n being the microservices under observations) flattened out to rowvectors ]
     - 3 Hidden layer [Dimension 1500 hidden nodes, activation:  RelU]
     - 1 output layer [Dimensions : number of Microservices, activation : softmax (so it can be interpreted as probability)]

     We will train with Adam Algorithm


# Training the actual Model:

     - accounting service not really instrumented + wrongly doucumented (written in c# and not go)
          ==> transformed data not really usable
          ==> every trace consists only of one span


# The Choice of the Background Task

     - the analysis microservice should function after the 
     - lightweight form of a synchronous communication

# Distributed tracing and Microservice Comminication Patterns
     - child_of ==> synchronous , blocking request response communication
     - follows_from ==> event-driven , asynchronous?


     
     







     




          


