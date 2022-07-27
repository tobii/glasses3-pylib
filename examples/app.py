import asyncio
import logging
import os
from typing import Dict, Optional, Tuple

import dotenv
from kivy.app import App
from kivy.lang.builder import Builder
from kivy.properties import BooleanProperty
from kivy.uix.label import Label
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleview.layout import LayoutSelectionBehavior
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.screenmanager import Screen, ScreenManager

from glasses3 import Glasses3, connect_to_glasses
from glasses3.g3typing import Hostname, SignalBody
from glasses3.zeroconf import EventKind, G3Service, G3ServiceDiscovery

logging.basicConfig(level=logging.DEBUG)

dotenv.load_dotenv()  # type: ignore
g3_hostname = Hostname(os.environ["G3_HOSTNAME"])

# fmt: off
Builder.load_string("""
#:import NoTransition kivy.uix.screenmanager.NoTransition

<DiscoveryScreen>:
    BoxLayout:
        SelectableList:
            id: services
        Button:
            text: "Connect"
            on_press: app.connect()

<ControlScreen>:
    BoxLayout:
        orientation: 'vertical'
        BoxLayout:
            size_hint: 1, None
            height: dp(50)
            Button:
                text: "Recorder"
                on_press: app.switch_control_screen_to("recorder")
            Button:
                text: "Live"
                on_press: app.switch_control_screen_to("live")
            Button:
                background_color: (0.6, 0.6, 1, 1)
                text: "Disconnect"
                on_press:
                    app.disconnect()
        ScreenManager:
            id: sm
            transition: NoTransition()

<RecorderScreen>:
    BoxLayout:
        BoxLayout:
            orientation: 'vertical'
            Label:
                id: recorder_status
                text: "Status:"
            Button:
                text: "Start"
                on_press: app.send_control_event("record")
            Button:
                text: "Stop"
                on_press: app.send_control_event("stop")
        SelectableList:
            id: recordings

<LiveScreen>:
    BoxLayout:
        Label:
            text: "Here you can see your glasses in action."

<SelectableList>:
    viewclass: 'SelectableLabel'
    SelectableRecycleBoxLayout:
        id: selectables
        default_size: None, dp(70)
        default_size_hint: 1, None
        size_hint_y: None
        height: self.minimum_height
        orientation: 'vertical'

<SelectableLabel>:
    canvas.before:
        Color:
            rgba: (.0, 0.9, .1, .3) if self.selected else (0, 0, 0, 1)
        Rectangle:
            pos: self.pos
            size: self.size
"""
)
# fmt: on


class SelectableRecycleBoxLayout(LayoutSelectionBehavior, RecycleBoxLayout):
    pass


class SelectableLabel(RecycleDataViewBehavior, Label):
    index = None
    selected = BooleanProperty(False)
    selectable = BooleanProperty(True)

    def refresh_view_attrs(self, rv, index, data):
        """Catch and handle the view changes"""
        self.index = index
        return super().refresh_view_attrs(rv, index, data)

    def on_touch_down(self, touch):
        """Add selection on touch down"""
        if super().on_touch_down(touch):
            return True
        if self.collide_point(*touch.pos) and self.selectable:
            return self.parent.select_with_touch(self.index, touch)

    def apply_selection(self, rv, index, is_selected):
        """Respond to the selection of items in the view."""
        self.selected = is_selected
        if is_selected:
            print("selection changed to {0}".format(rv.data[index]))
        else:
            print("selection removed for {0}".format(rv.data[index]))


class SelectableList(RecycleView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.data = []


class DiscoveryScreen(Screen):
    pass


class ControlScreen(Screen):
    pass


class RecorderScreen(Screen):
    pass


class LiveScreen(Screen):
    pass


class G3App(App, ScreenManager):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.tasks = set()
        self.screen_by_name: Dict[str, Screen] = dict()
        self.control_events = asyncio.Queue()

    def connect(self):
        selected = self.screen_by_name[
            "discovery"
        ].ids.services.ids.selectables.selected_nodes
        if len(selected) <= 0:
            print("Please choose a Glasses3 unit to connect.")  # TODO: print in gui
        else:
            hostname = self.screen_by_name["discovery"].ids.services.data[selected[0]][
                "id"
            ]
            self.backend_control_task = self.create_task(self.backend_control(hostname))
            self.switch_to(self.screen_by_name["control"], direction="left")

    def disconnect(self):
        self.backend_control_task.cancel()
        self.create_task(self.stop_update_recordings())
        self.create_task(self.stop_update_recorder_status())
        self.switch_to(self.screen_by_name["discovery"], direction="right")
        self.clear_control_screen()

    def clear_control_screen(self):
        self.control_screen.ids.sm.screen_by_name["recorder"].ids.recordings.data = []

    def switch_control_screen_to(self, screen: str):
        self.control_screen.ids.sm.switch_to(
            self.control_screen.ids.sm.screen_by_name[screen]
        )

    def recorder_screen_add_recording(self, recording, atEnd=False):
        recorder_screen = self.control_sm.screen_by_name["recorder"]
        if atEnd == True:
            recorder_screen.ids.recordings.data.append({"text": str(recording)})
        else:
            recorder_screen.ids.recordings.data.insert(0, {"text": str(recording)})

    def recorder_screen_remove_recording(self, recording):
        recorder_screen = self.control_sm.screen_by_name["recorder"]
        recorder_screen.ids.recordings.data = [
            recording_data
            for recording_data in recorder_screen.ids.recordings.data
            if recording_data["text"] != recording
        ]

    def recorder_screen_set_recording(self):
        recorder_screen = self.control_sm.screen_by_name["recorder"]
        recorder_screen.ids.recorder_status.text = "Status: Recording"

    def recorder_screen_set_not_recording(self):
        recorder_screen = self.control_sm.screen_by_name["recorder"]
        recorder_screen.ids.recorder_status.text = "Status: Not recording"

    def build(self):
        self.screen_by_name["discovery"] = DiscoveryScreen(name="discovery")
        self.screen_by_name["control"] = ControlScreen(name="control")
        self.add_widget(self.screen_by_name["discovery"])
        self.add_widget(self.screen_by_name["control"])

        self.control_screen = self.screen_by_name["control"]
        self.control_screen.ids.sm.screen_by_name = dict()
        self.control_sm = self.control_screen.ids.sm

        self.control_sm.screen_by_name["recorder"] = RecorderScreen(name="recorder")
        self.control_sm.screen_by_name["live"] = LiveScreen(name="live")
        self.control_sm.add_widget(self.control_sm.screen_by_name["recorder"])
        self.control_sm.add_widget(self.control_sm.screen_by_name["live"])

        return self

    def on_start(self):
        self.create_task(self.backend_discovery())

    async def backend_discovery(self):
        async with G3ServiceDiscovery.listen() as service_listener:
            while True:
                await self.handle_service_event(await service_listener.events.get())

    async def handle_service_event(self, event: Tuple[EventKind, G3Service]):
        match event:
            case (EventKind.ADDED, service):
                self.add_service(
                    service.hostname, service.ipv4_address, service.ipv6_address
                )
            case (EventKind.UPDATED, service):
                self.update_service(
                    service.hostname, service.ipv4_address, service.ipv6_address
                )
            case (EventKind.REMOVED, service):
                self.remove_service(
                    service.hostname, service.ipv4_address, service.ipv6_address
                )

    def add_service(self, hostname: str, ipv4: Optional[str], ipv6: Optional[str]):
        self.screen_by_name["discovery"].ids.services.data.append(
            {"id": hostname, "text": f"{hostname}\n{ipv4}\n{ipv6}"}
        )

    def update_service(self, hostname: str, ipv4: Optional[str], ipv6: Optional[str]):
        data_list = self.screen_by_name["discovery"].ids.services.data
        for service in data_list:
            if service["id"] == hostname:
                service["text"] = f"{hostname}\n{ipv4}\n{ipv6}"

    def remove_service(self, hostname: str, ipv4: Optional[str], ipv6: Optional[str]):
        self.screen_by_name["discovery"].ids.services.data = [
            service
            for service in self.screen_by_name["discovery"].ids.services.data
            if service["id"] != hostname
        ]

    def send_control_event(self, event: str):
        self.control_events.put_nowait(event)

    async def backend_control(self, hostname):
        async with connect_to_glasses(hostname) as g3:
            async with g3.recordings.keep_updated_in_context():
                await self.start_update_recordings(g3)
                await self.start_update_recorder_status(g3)
                while True:
                    await self.handle_control_event(g3, await self.control_events.get())

    async def handle_control_event(self, g3: Glasses3, event: str):
        print(event)
        match event:
            case "record":
                await g3.recorder.start()
            case "stop":
                await g3.recorder.stop()

    async def start_update_recorder_status(self, g3: Glasses3):
        if await g3.recorder.get_created() != None:
            self.recorder_screen_set_recording()
        else:
            self.recorder_screen_set_not_recording()
        (
            recorder_started_queue,
            self.unsubscribe_to_recorder_started,
        ) = await g3.recorder.subscribe_to_started()
        (
            recorder_stopped_queue,
            self.unsubscribe_to_recorder_stopped,
        ) = await g3.recorder.subscribe_to_stopped()
        self.handle_recorder_started_task = self.create_task(
            self.handle_recorder_started(recorder_started_queue)
        )
        self.handle_recorder_stopped_task = self.create_task(
            self.handle_recorder_stopped(recorder_stopped_queue)
        )

    async def stop_update_recorder_status(self):
        await self.unsubscribe_to_recorder_started
        await self.unsubscribe_to_recorder_stopped
        self.handle_recorder_started_task.cancel()
        self.handle_recorder_stopped_task.cancel()

    async def handle_recorder_started(
        self, recorder_started_queue: asyncio.Queue[SignalBody]
    ):
        while True:
            await recorder_started_queue.get()
            self.recorder_screen_set_recording()

    async def handle_recorder_stopped(
        self, recorder_stopped_queue: asyncio.Queue[SignalBody]
    ):
        while True:
            await recorder_stopped_queue.get()
            self.recorder_screen_set_not_recording()

    async def start_update_recordings(self, g3: Glasses3):
        for child in g3.recordings:
            self.recorder_screen_add_recording(child.uuid, atEnd=True)
        (
            child_added_queue,
            self.unsubscribe_to_child_added,
        ) = await g3.recordings.subscribe_to_child_added()
        (
            child_removed_queue,
            self.unsubscribe_to_child_removed,
        ) = await g3.recordings.subscribe_to_child_removed()
        self.handle_added_recordings_task = self.create_task(
            self.handle_added_recordings(child_added_queue)
        )
        self.handle_removed_recordings_task = self.create_task(
            self.handle_removed_recordings(child_removed_queue)
        )

    async def stop_update_recordings(self):
        await self.unsubscribe_to_child_added
        await self.unsubscribe_to_child_removed
        self.handle_added_recordings_task.cancel()
        self.handle_removed_recordings_task.cancel()

    async def handle_added_recordings(self, child_added_queue):
        while True:
            recording = (await child_added_queue.get())[0]
            self.recorder_screen_add_recording(recording)

    async def handle_removed_recordings(self, child_removed_queue):
        while True:
            recording = (await child_removed_queue.get())[0]
            self.recorder_screen_remove_recording(recording)

    def create_task(self, coro, name=None) -> asyncio.Task:
        task = asyncio.create_task(coro, name=name)
        self.tasks.add(task)
        task.add_done_callback(self.tasks.remove)
        return task


if __name__ == "__main__":
    app = G3App()
    asyncio.run(app.async_run())
