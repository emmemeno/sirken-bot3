import timehandler as timeh
import config


def message_cut(input_text: str, limit: int):
    """
    Function that take a string as argument and breaks it in smaller chunks
    :param input_text: str
    :param limit: int
    :return: output: list()
    """

    output = list()

    while len(input_text) > limit:

        # find a smart new limit based on newline...
        smart_limit = input_text[0:limit].rfind('\n') + 1
        if smart_limit == -1:
            # ...or find a smart new limit based on blank space
            smart_limit = input_text[0:limit].rfind(' ') + 1
        output.append(input_text[0:smart_limit])
        input_text = input_text[smart_limit:]

    output.append(input_text)
    return output


def prettify(text: str, my_type="BLOCK"):

    output_text = list()
    prefix = postfix = ""
    cut_text = message_cut(text, config.MAX_MESSAGE_LENGTH)

    for chunk in cut_text:
        if my_type == "BLOCK":
            prefix = postfix = "```\n"
        elif my_type == "CSS":
            prefix = "```css\n"
            postfix = "```\n"

        elif my_type == "SINGLE":
            prefix = "`\n"
            postfix = prefix
        output_text.append(prefix + chunk + postfix)

    return output_text


def time_remaining(name, eta, plus_minus, window, spawns, accuracy, target, snippet):
    now = timeh.now()
    postfix = ""
    prefix = ""
    output = "[" + name + "] "
    approx = ""
    if accuracy <= 0 or spawns == 1:
        approx = "{roughly} "
    if accuracy <= -1 or spawns > 1:
        approx = "{very roughly} "
    if not plus_minus:
        if now > eta:
            output += "ToD is too old. "
        else:
            output += "will %sspawn in %s " % (approx, timeh.countdown(now, eta))
    else:
        if now > window['end']:
            output += "window is closed "
        elif now < window['start']:
            output += "window will %sopen in %s " % (approx, timeh.countdown(now, eta))
        elif window['start'] <= now <= window['end']:
            prefix = ""
            postfix = "## "
            output += "is %sin window until %s " % (approx, timeh.countdown(now, eta))

    if spawns >= 1:
        output += "(%s respawn since last update) " % spawns
    if target:
        postfix += ".target"
    if snippet:
        snippet = "-\n%s" % snippet

    return prefix + output + postfix + "\n" + snippet


def detail(name, tod, pop, signed_tod, signed_pop, respawn_time, plus_minus, tags,
           window_start, window_end, accuracy, eta, snippet, trackers):
    output = "%s\n" % name
    output += "=" * len(name) + "\n\n"
    approx = ""
    if accuracy == 0:
        approx = "'roughly' "
    print_tags = ""
    for tag in tags:
        print_tags += "%s " % tag
    if print_tags:
        print_tags = print_tags[:-1]

    output += "{LAST TOD}      [%s] signed by %s\n" \
              "{LAST POP}      [%s] signed by %s\n" \
              "{RESPAWN TIME}  [%s±%s]\n" \
              "{TAGS}          [%s]\n" \
              % (tod, simple_username(signed_tod),
                 pop, simple_username(signed_pop),
                 respawn_time, plus_minus,
                 print_tags)
    if plus_minus:
        output += "{WINDOW OPEN}   [%s]\n" \
                  "{WINDOW CLOSE}  [%s]\n" \
                  % (window_start, window_end)

    output += "{LAST SNIPPET}  [%s]\n" % snippet
    if trackers:
        output += "{TRACKERS}      [\n"
        for tracker in trackers:
            output += "%s - " % tracker
        output = output[0:-3]
        output += "]"
    return output


def tracker_list(merb, timezone):
    output = ""
    for tracker in reversed(merb.trackers):
        tracker_name = next(iter(tracker))
        tracker_start = timeh.change_tz(timeh.naive_to_tz( tracker[tracker_name]["time_start"], "UTC"), timezone)
        tracker_stop = False
        tracker_mode = tracker[tracker_name]["mode"]
        if "time_stop" in tracker[tracker_name]:
            tracker_stop = timeh.change_tz(timeh.naive_to_tz( tracker[tracker_name]["time_stop"], "UTC"), timezone)
            output += "  "
        else:
            output += "# "
        output += "%s - starts at {%s %s} " % (tracker_name, tracker_start.strftime(config.DATE_FORMAT_PRINT), timezone)
        if tracker_stop:
            output += "stops at {%s %s} " % (tracker_stop.strftime(config.DATE_FORMAT_PRINT), timezone)
            output += "(%s) " % timeh.countdown(tracker_start, tracker_stop)
        else:
            if timeh.naive_to_tz(timeh.now(), "UTC") < tracker_start:
                virtual_end = tracker_start
            else:
                virtual_end = timeh.naive_to_tz(timeh.now(), "UTC")
            output += "(%s so far) " % timeh.countdown(tracker_start, virtual_end)
        if tracker_mode:
            output += ".%s" % tracker_mode
        output += "\n"
    if not output:
        output = "Empty!\n"

    return output


def track_recap(merb, timezone, merb_updated=False):
    output_content = "\n\n"
    if merb_updated == "pop":
        output_content += "[%s] popped at {%s %s}\n" % (merb.name, merb.pop.strftime(config.DATE_FORMAT_PRINT), timezone)
    elif merb_updated == "tod":
        output_content += "[%s] died at {%s %s}\n" % (merb.name, merb.tod.strftime(config.DATE_FORMAT_PRINT), timezone)
    else:
        output_content += "[%s] (%s) " % (merb.name, len(merb.get_active_trackers()))
        if timeh.now() < merb.window['start']:
            output_content += "window will open in %s\n" % timeh.countdown(timeh.now(), merb.eta)
        elif merb.window['start'] <= timeh.now() <= merb.window['end']:
            output_content += "in .window for the next %s\n" % timeh.countdown(timeh.now(), merb.eta)
        else:
            output_content += "window is closed. Please update tod/pop\n"
    output_content += "-" * (len(output_content) - 3)
    output_content += "\n"
    output_content += tracker_list(merb, timezone )
    return output_content


def last_update(name, last, mode="tod"):
    output = "[" + name + "] last %s {%s}\n" % (mode, last)
    return output


def output_list(content: list):
        output = ""
        for line in content:
            output += line
        if output == "":
            output = "Empty!"
        return output


def meta(name, merb_alias, merb_tag):
    output = "[%s] " % name
    for alt in merb_alias:
        output += "{%s} " % alt
    for tag in merb_tag:
        output += "#%s " % tag
    output += "\n"
    return output


def alias(name, merb_alias):
    output = "[%s] " % name
    for alt in merb_alias:
        output += "{%s} " % alt
    output += "\n"
    return output


def simple_username(user: str):
    new_user = user.split("#")
    if new_user:
        return new_user[0]
    else:
        return user
