import modules.dashboard
import inspect

print("MODULE FILE:")
print(modules.dashboard.__file__)

print("\nSOURCE:")
print(inspect.getsource(modules.dashboard.show_dashboard))