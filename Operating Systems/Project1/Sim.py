import math
import random
import pandas as pd

#---------------------------------------------------------------------------#
class CPU: 
    def __init__(self):
        self.clock = 0
        self.busy = False
#---------------------------------------------------------------------------#
      
#---------------------------------------------------------------------------#
class Disk:
    def __init__(self):
        self.busy = False
#---------------------------------------------------------------------------#
      
#---------------------------------------------------------------------------#
class Process:
    last_pid = 0  
    def __init__(self):
        self.arrival_time = 0
        self.cpu_service_time = 0
        self.disk_service_time = 0
        self.cpu_done = False
        self.disk_done = False

        self.pid = Process.last_pid + 1  # Assign a unique PID to the process
        Process.last_pid = self.pid  # Update the last assigned PID
#---------------------------------------------------------------------------#
      
#---------------------------------------------------------------------------#
class Event:
    def __init__(self, process=None):
        self.time = 0
        self.type = ''
        self.process = process
#---------------------------------------------------------------------------#
      
#---------------------------------------------------------------------------#
class Simulator:
    def __init__(self, average_arrival_rate, average_CPU_service_time, average_Disk_service_time):
        self.cpu = CPU()
        self.disk = Disk()
        self.average_arrival_rate = average_arrival_rate
        self.average_CPU_service_time = average_CPU_service_time
        self.average_Disk_service_time = average_Disk_service_time
        self.end_condition = 10000

        self.ready_queue = []
        self.disk_queue = []
        self.event_queue = []
        self.debug = False

        self.num_disk_processes = 0
        self.number_completed_processes = 0
        self.total_turnaround_time = 0
        self.total_cpu_service_times = 0
        self.total_disk_service_times = 0
        self.sum_num_of_proc_in_readyQ = 0
        self.sum_num_of_proc_in_diskQ = 0
#---------------------------------------------------------------------------#
    def first_come_first_serve(self):
        # Generate and schedule the first process
        first_process = self.generateProcess()
        if self.debug:
            print(f"First process generated with PID={first_process.pid} and arrival time={first_process.arrival_time}\n\n")
        first_event = self.generateEvent(first_process.arrival_time, "ARR", first_process)

        if self.debug:
            print(f"First event scheduled: Type={first_event.type}, Time={first_event.time}, Process PID={first_event.process.pid}\n\n")
        self.event_queue.append(first_event)

        while self.number_completed_processes < self.end_condition:
            if self.debug:
                print("\n\n\n\n")
                print(f"Current simulation clock: {self.cpu.clock}")
                print(f"Number of completed processes: {self.number_completed_processes}")
                print(f"Event queue size: {len(self.event_queue)}, Ready queue size: {len(self.ready_queue)}, Disk queue size: {len(self.disk_queue)}\n\n")

            # Sort the event queue by time
            self.event_queue.sort(key=lambda x: x.time)

            # Take the next event from the event queue
            event = self.event_queue.pop(0)
            if self.debug:
                print(f"Processing event: Type={event.type}, Time={event.time}, Process PID={event.process.pid}\n\n\n\n")

            # Update the clock to the occurring event time
            self.cpu.clock = event.time

            # Process the event based on its type
            if event.type == "ARR":
                self.handleArrival(event)
            elif event.type == "DISK_ARR":
                self.handleDiskArival(event)
            elif event.type == "DISK_DEP":
                self.handleDiskDeparture(event)
            elif event.type == "DEP":
                self.handleDeparture(event)
            else:
                print("Invalid event type") if self.debug else None

            if self.debug:
                print(f"\n\nPost-event processing: Simulation clock: {self.cpu.clock}, Ready queue size: {len(self.ready_queue)}, Disk queue size: {len(self.disk_queue)}")

        # Calculate and report the metrics
        avg_turn_around_time = (self.total_turnaround_time / self.end_condition)
        throughput = (self.end_condition / self.cpu.clock)
        cpu_utilization = 100 * (self.total_cpu_service_times / self.cpu.clock)
        disk_utilization = 100 * (self.total_disk_service_times / self.cpu.clock)
        avg_num_processes_in_readyQ = self.sum_num_of_proc_in_readyQ / self.end_condition
        avg_num_processes_in_diskQ = self.sum_num_of_proc_in_diskQ / self.end_condition

        self.report(avg_turn_around_time, throughput, cpu_utilization, disk_utilization, avg_num_processes_in_readyQ, avg_num_processes_in_diskQ)  
#---------------------------------------------------------------------------#
    def handleArrival(self, event):
        self.logArrivalDetails(event)
    
        if not self.cpu.busy:
            self.scheduleDeparture(event.process)
        else:
            self.addToReadyQueue(event.process)

        if not event.process.disk_done:
            self.scheduleNextArrival()

        self.logPostArrivalState()
#---------------------------------------------------------------------------#
    def logArrivalDetails(self, event):
        if self.debug:
            print(f"Handling Arrival at time={self.cpu.clock}, Process ID={event.process.pid}, CPU Busy={self.cpu.busy}, Ready Queue Size={len(self.ready_queue)}\n\n")
#---------------------------------------------------------------------------#
    def scheduleDeparture(self, process):
        self.cpu.busy = True
        depart_time = self.cpu.clock + process.cpu_service_time   
        departure_event = self.generateEvent(depart_time, "DEP", process)
        self.event_queue.append(departure_event)

        if self.debug:
            print(f"Scheduled Event DEP at time={departure_event.time}, Process ID={process.pid}\n\n\n\n")
#---------------------------------------------------------------------------#
    def addToReadyQueue(self, process):
        self.ready_queue.append(process)

        if self.debug:
            print(f"Process ID={process.pid} added to ready queue\n\n\n\n")
#---------------------------------------------------------------------------#
    def scheduleNextArrival(self):
        self.num_disk_processes += 1
        new_process = self.generateProcess()
        new_arrival_event = self.generateEvent(new_process.arrival_time, "ARR", new_process)
        self.event_queue.append(new_arrival_event)

        if self.debug:
            print(f"Scheduled next arrival at time={new_arrival_event.time}, Process ID={new_process.pid}\n\n\n\n")
#---------------------------------------------------------------------------#
    def logPostArrivalState(self):
        if self.debug:
            print(f"Post-Arrival: CPU Busy={self.cpu.busy}, Ready Queue Size={len(self.ready_queue)}, Event Queue Size={len(self.event_queue)}\n\n")    
#---------------------------------------------------------------------------#
    def handleDiskArival(self, event):
        if self.debug:
            print(f"Handling Disk Arrival at time={self.cpu.clock}, Process ID={event.process.pid}, Disk Busy={self.disk.busy}, Disk Queue Size={len(self.disk_queue)}")

        if not self.disk.busy:
            # Disk is not busy, process can be served
            self.disk.busy = True
            depart_time = self.cpu.clock + event.process.disk_service_time
            disk_departure_event = self.generateEvent(depart_time, "DISK_DEP", event.process)
            self.event_queue.append(disk_departure_event)

            if self.debug:
                print(f"Scheduled disk departure at time={disk_departure_event.time}, Process ID={event.process.pid}\n\n\n\n")
        else:
            # Disk is busy, process goes to disk queue
            self.disk_queue.append(event.process)

            if self.debug:
                print(f"Process ID={event.process.pid} added to disk queue\n\n\n\n")
                print(f"Post-Disk Arrival: Disk Busy={self.disk.busy}, Disk Queue Size={len(self.disk_queue)}, Event Queue Size={len(self.event_queue)}\n\n\n\n\n\n")
#---------------------------------------------------------------------------#
    def handleDiskDeparture(self, event):
        if self.debug:
            print(f"Handling Disk Departure at time={self.cpu.clock}, Process ID={event.process.pid}, Disk Busy={self.disk.busy}, Disk Queue Size={len(self.disk_queue)}\n\n")

        # Process got served, take the service time
        self.total_disk_service_times += event.process.disk_service_time

        # Schedule an arrival event for the process that just finished disk service
        event.process.disk_done = True
        cpu_arrival_time = self.cpu.clock
        cpu_arrival_event = self.generateEvent(cpu_arrival_time, "ARR", event.process)
        self.event_queue.append(cpu_arrival_event)

        if self.disk_queue:  # If there are processes in the disk queue
            # Schedule the next process in the disk queue
            self.disk.busy = True
            next_process = self.disk_queue.pop(0)

            depart_time = self.cpu.clock + next_process.disk_service_time
            disk_departure_event = self.generateEvent(depart_time, "DISK_DEP", next_process)
            self.event_queue.append(disk_departure_event)
    
            if self.debug:
                print(f"Scheduled next disk departure at time={disk_departure_event.time}, Process ID={next_process.pid}\n\n\n\n")
        else:
            self.disk.busy = False
            if self.debug:
                print(f"Disk is now idle\n\n\n\n")

        if self.debug:
            print(f"Post-Disk Departure: Disk Busy={self.disk.busy}, Disk Queue Size={len(self.disk_queue)}, Event Queue Size={len(self.event_queue)}\n\n\n\n")
#---------------------------------------------------------------------------#
    def handleDeparture(self, event):
        if self.debug:
            print(f"Handling CPU Departure at time={self.cpu.clock}, Process ID={event.process.pid}, CPU Busy={self.cpu.busy}, Ready Queue Size={len(self.ready_queue)}\n\n")

        # Process got served, take the service time
        self.total_cpu_service_times += event.process.cpu_service_time

        # Determine whether the process completes or moves to disk
        if random.uniform(0, 1) <= 0.6:
            self.number_completed_processes += 1
            self.total_turnaround_time += (self.cpu.clock - event.process.arrival_time)
            self.sum_num_of_proc_in_readyQ += len(self.ready_queue)
            self.sum_num_of_proc_in_diskQ += len(self.disk_queue)
            if self.debug:
                print(f"Process ID={event.process.pid} completed at time={self.cpu.clock}\n\n\n\n")
        else:
            # Schedule disk arrival event
            disk_arrival_time = self.cpu.clock
            disk_arrival_event = self.generateEvent(disk_arrival_time, "DISK_ARR", event.process)
            self.event_queue.append(disk_arrival_event)

        # Schedule next departure if ready queue is not empty
        if self.ready_queue:
            next_process = self.ready_queue.pop(0)
            self.cpu.busy = True
            depart_time = self.cpu.clock + next_process.cpu_service_time
            departure_event = self.generateEvent(depart_time, "DEP", next_process)
            self.event_queue.append(departure_event)
            if self.debug:
                print(f"Scheduled next departure at time={departure_event.time}, Process ID={next_process.pid}\n\n\n\n")
        else:
            # Mark CPU as idle if ready queue is empty
            self.cpu.busy = False
            if self.debug:
                print(f"CPU is now idle\n\n\n\n")

        if self.debug:
            print(f"Post-Departure: CPU Busy={self.cpu.busy}, Ready Queue Size={len(self.ready_queue)}, Completed Processes={self.number_completed_processes}\n\n\n\n")
#---------------------------------------------------------------------------#
    def generateProcess(self):
        process = Process()

        # Calculate arrival time using exponential distribution
        arrival_time = self.cpu.clock + (math.log(1 - float(random.uniform(0, 1))) / (-self.average_arrival_rate))
        process.arrival_time = arrival_time

        # Calculate CPU service time using exponential distribution
        cpu_lambda = 1.0 / self.average_CPU_service_time
        cpu_service_time = math.log(1 - float(random.uniform(0, 1))) / (-cpu_lambda)
        process.cpu_service_time = cpu_service_time

        # Calculate Disk service time using exponential distribution
        disk_lambda = 1.0 / self.average_Disk_service_time
        disk_service_time = math.log(1 - float(random.uniform(0, 1))) / (-disk_lambda)
        process.disk_service_time = disk_service_time

        return process
#---------------------------------------------------------------------------#
    def generateEvent(self, time, type, process):
        event = Event(process=process)
        event.time = time
        event.type = type

        return event
#---------------------------------------------------------------------------#
    def run(self):
        # Start scheduler
        self.first_come_first_serve()
#---------------------------------------------------------------------------#
    def report(self, avg_turn_around_time, throughput, cpu_utilization, disk_utilization, avg_num_processes_in_readyQ, avg_num_processes_in_diskQ):
        report_lines = self.generateReportLines(avg_turn_around_time, throughput, cpu_utilization, disk_utilization, avg_num_processes_in_readyQ, avg_num_processes_in_diskQ)
        self.printReport(report_lines)
        self.writeToFile(report_lines)
#---------------------------------------------------------------------------#
    def generateReportLines(self, avg_turn_around_time, throughput, cpu_utilization, disk_utilization, avg_num_processes_in_readyQ, avg_num_processes_in_diskQ):
        report_lines = [
            f"{'Metrics Report λ: ':}{self.average_arrival_rate:}",
            f"{'='*40}",
            f"{'Throughput:':<30}{throughput:>10.4f} processes/unit time",
            f"{'CPU Utilization:':<30}{cpu_utilization:>10.4f}%",
            f"{'Disk Utilization:':<30}{disk_utilization:>10.4f}%",
            f"{'Avg. Processes in Ready Queue:':<30}{avg_num_processes_in_readyQ:>10.4f}",
            f"{'Avg. Processes in Disk Queue:':<30}{avg_num_processes_in_diskQ:>10.4f}",
            f"{'Avg. Turnaround Time:':<30}{avg_turn_around_time:>10.4f} seconds",
            f"{'='*40}"
        ]
        return report_lines
#---------------------------------------------------------------------------#
    def printReport(self, report_lines):
        for line in report_lines:
            print(line)
        print('\n\n\n') if self.debug else None
        print(f"{'Compare to':^40}") if self.debug else None
        print(f"{'='*40}") if self.debug else None
        print(f"{'Throughput:':<30}{12} processes/unit time") if self.debug else None      
        print(f"{'CPU Utilization:':<30}{40}%") if self.debug else None
        print(f"{'Disk Utilization:':<30}{48}%") if self.debug else None
        print(f"{'Avg. Processes in Ready Queue:':<30}{0.2666}") if self.debug else None
        print(f"{'Avg. Processes in Disk Queue:':<30}{0.44}") if self.debug else None
        print(f"{'Avg. Turnaround Time:':<30}{0.132} seconds") if self.debug else None
        print(f"{'='*40}") if self.debug else None
        print('\n\n\n') if self.debug else None
#---------------------------------------------------------------------------#
    def writeToFile(self, report_lines):
        file_mode = 'w' if self.average_arrival_rate == 1 else 'a'
        with open('Results/simulation_report.txt', file_mode, encoding='utf-8') as file:
            for line in report_lines:
                file.write(line + '\n')
#---------------------------------------------------------------------------#
    def excelReport(self, avg_turn_around_time, throughput, cpu_utilization, disk_utilization, avg_num_processes_in_readyQ, avg_num_processes_in_diskQ):
        metrics = {
            "Metric": [
            "Throughput", 
            "CPU Utilization", 
            "Disk Utilization", 
            "Avg. Processes in Ready Queue", 
            "Avg. Processes in Disk Queue", 
            "Avg. Turnaround Time"
            ],
            "Value": [
                f"{throughput:.4f} processes/unit time",
                f"{cpu_utilization:.4f}%",
                f"{disk_utilization:.4f}%",
                f"{avg_num_processes_in_readyQ:.4f}",
                f"{avg_num_processes_in_diskQ:.4f}",
                f"{avg_turn_around_time:.4f} seconds"
            ]
        }
    
        # Convert the metrics dictionary into a DataFrame
        df = pd.DataFrame(metrics)
    
        # Define the Excel file path and sheet name
        excel_file = 'Results/simulation_metrics.xlsx'
        sheet_name = f'λ_{self.average_arrival_rate}'
    
        # Write to Excel with different behavior based on the arrival rate (λ)
        if self.average_arrival_rate == 1:
            # For λ=1, overwrite any existing file or create a new one
            with pd.ExcelWriter(excel_file, engine='openpyxl', mode='w') as writer:
                df.to_excel(writer, sheet_name=sheet_name, index=False)
        elif self.average_arrival_rate < 31 and self.average_arrival_rate > 1:
            # For 1<λ<31, append to existing file or create a new one
            try:
                with pd.ExcelWriter(excel_file, engine='openpyxl', mode='a') as writer:
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
            except FileNotFoundError:
                # If the file does not exist, create it
                with pd.ExcelWriter(excel_file, engine='openpyxl', mode='w') as writer:
                    df.to_excel(writer, sheet_name=sheet_name, index=False)


    def get_metrics_df(self, avg_turn_around_time, throughput, cpu_utilization, disk_utilization, avg_num_processes_in_readyQ, avg_num_processes_in_diskQ):
        metrics = {
            "Lambda": self.average_arrival_rate,
            "Throughput": throughput,
            "CPU Utilization": cpu_utilization,
            "Disk Utilization": disk_utilization,
            "Avg. Processes in Ready Queue": avg_num_processes_in_readyQ,
            "Avg. Processes in Disk Queue": avg_num_processes_in_diskQ,
            "Avg. Turnaround Time": avg_turn_around_time
        }
        return pd.DataFrame([metrics])