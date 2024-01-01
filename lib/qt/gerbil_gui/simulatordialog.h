#ifndef SIMULATORDIALOG_H
#define SIMULATORDIALOG_H

#include <QDialog>

namespace Ui {
class SimulatorDialog;
}

class SimulatorDialog : public QDialog
{
    Q_OBJECT

public:
    explicit SimulatorDialog(QWidget *parent = 0);
    ~SimulatorDialog();

private:
    Ui::SimulatorDialog *ui;
};

#endif // SIMULATORDIALOG_H
