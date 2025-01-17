class Configure():
    def __init__(self):
        with open("config.txt", "r") as file:
            self.sections = {}
            bracket_counter = 0
            current_section = ""
            for line in file:
                if line.strip() == "[":
                    bracket_counter += 1
                    continue
                elif line.strip() == "]":
                    bracket_counter -= 1
                    continue
                if bracket_counter == 0:
                    name = line.strip().lower()
                    self.sections[name] = {}
                    current_section = name
                else:
                    line_splitted = line.strip().split(" ")
                    self.sections[current_section][line_splitted[0].lower()] = line_splitted[2:]

    def Ethernet(self):
        result = self.sections["ethernet"]
        result["source"] = result["source"][0]
        result["ipg"] = float(result["ipg"][0]) * 10**(-9)
        result["payload"] = int(result["payload"][0])
        return result
    
    def PCIe(self):
        result = self.sections["pcie"]
        result["lanes"] = int(result["lanes"][0])
        result["throughput"] = float(result["throughput"][0]) * 10**9
        return result
    
    def Core(self):
        result = self.sections["core"]
        result["frequency"] = float(result["frequency"][0]) * 10**9
        result["ttl_level"] = float(result["ttl_level"][0])
        return result
    
    def RAM(self):
        result = self.sections["ram"]
        result["size"] = float(result["size"][0]) * 10**9
        result["os_size"] = float(result["os_size"][0]) * 10**9
        return result
    
    def Processor(self):
        result = self.sections["processor"]
        result["number_of_cores"] = int(result["number_of_cores"][0])
        return result
    
    def ProcChannels(self, profile):
        section = self.sections[profile.lower()]
        result = []
        for s in section["channels"]:
            parsed = s.strip("()").split(",")
            result.append([int(c) for c in parsed])
        return result
