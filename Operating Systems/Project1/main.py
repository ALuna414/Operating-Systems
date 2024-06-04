import sys
from Sim import Simulator
import pandas as pd
import matplotlib.pyplot as plt
from imgcat import imgcat  # Import imgcat

all_metrics_data = []
def plot_individual_metrics(dataframe):
   metrics = ["Lambda", "Throughput", "CPU Utilization", "Disk Utilization", "Avg. Processes in Ready Queue", "Avg. Processes in Disk Queue", "Avg. Turnaround Time"]
   for metric in metrics:
      if metric != "Lambda":
         plt.figure(figsize=(5, 5))
         plt.plot(dataframe["Lambda"], dataframe[metric], marker='o', color='b', label=metric)
         plt.title(f"{metric} vs lambda")
         plt.grid()
         plt.legend()
         plt.savefig(f"Results/Graphs/{metric}_vs_lambda.png")
         plt.savefig(f"Results/Graphs/{metric}_vs_lambda.png")
         imgcat(f"Results/Graphs/{metric}_vs_lambda.png")  # Display the image in the terminal

if __name__ == "__main__":
   # Check if the correct number of arguments are provided
   if len(sys.argv) != 4:
      print("Usage: python main.py <average_arrival_rate> <average_CPU_service_time> <average_Disk_service_time>")
      print("Example: python main.py 12 .02 .06")
      sys.exit(1)  # Exit script if incorrect

   # Parse command-line arguments
   average_arrival_rate = float(sys.argv[1])
   average_CPU_service_time = float(sys.argv[2])
   average_Disk_service_time = float(sys.argv[3])

   if average_arrival_rate == 0:
      print("using defaults")
      # run the simulation with default values but varrying lambda 1 to 30
      for i in range(1, 31):
         sim = Simulator(i, average_CPU_service_time, average_Disk_service_time)
         sim.run()
         # Get the DataFrame of metrics for this run
         metrics_df = sim.get_metrics_df(sim.avg_turn_around_time, sim.throughput, sim.cpu_utilization, sim.disk_utilization, sim.avg_num_processes_in_readyQ, sim.avg_num_processes_in_diskQ)
         all_metrics_data.append(metrics_df)

      # Concatenate all metrics into a single DataFrame
      final_metrics_df = pd.concat(all_metrics_data, ignore_index=True)
      plot_individual_metrics(final_metrics_df)
      # Write the aggregated DataFrame to an Excel file
      excel_file_path = 'Results/final_simulation_metrics.xlsx'
      final_metrics_df.to_excel(excel_file_path, index=False)

   else:
      sim = Simulator(average_arrival_rate, average_CPU_service_time, average_Disk_service_time)
      
      sim.run()