import bisect
import re


def kallsyms_search(kallsyms_lines: list[str], address: int):
    # kallsyms lines looks like this
    #
    # ffffffffaa88e2f0 T kfree
    # ffffffffaa88e400 T __ksize
    # ffffffffaa88e530 T ksize
    key = lambda line: int(line.split()[0], 16) - 1
    return bisect.bisect_right(kallsyms_lines, address, key=key) - 1


def cut_addresses_from_log_line_kernel_callstack(line):
    my_regex = re.compile('0x([0-9a-fA-F]{16})')
    return my_regex.findall(line)


def get_lines_from_log(file_path):
    file_content = {}
    with open(file_path, 'r') as file:  # pylint: disable=unspecified-encoding
        for line in file:
            if ('kernel callstack' in line and '0x' in line) or 'Reactor stalled for' in line:
                file_content[line] = cut_addresses_from_log_line_kernel_callstack(line)
    return file_content


def get_kallsyms(path_to_kallsyms):
    with open(path_to_kallsyms, 'r') as file:  # pylint: disable=unspecified-encoding
        file_content = file.readlines()
    return file_content


def append_content_to_file(file_stream, content):
    file_stream.write(content + '\n')


def decode_kernel_callstacks(results_file='results.log', input_file='system.log', kallsyms_file='kallsyms',
                             clear_output_file=True):
    file_content = get_kallsyms(kallsyms_file)
    if clear_output_file:
        with open(results_file, 'w'):  # pylint: disable=unspecified-encoding
            print(f'clearing file {results_file}')

    with open(results_file, 'a') as file:  # pylint: disable=unspecified-encoding
        for full_line, stall in get_lines_from_log(input_file).items():
            append_content_to_file(file, '#' * 76)
            append_content_to_file(file, full_line)
            if 'Reactor stalled for' not in full_line:
                for frame in stall:
                    append_content_to_file(file, file_content[kallsyms_search(file_content, int(frame, 16))])
            append_content_to_file(file, '#' * 76)
