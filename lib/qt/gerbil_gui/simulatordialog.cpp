#include "simulatordialog.h"
#include "ui_simulatordialog.h"

SimulatorDialog::SimulatorDialog(QWidget *parent) :
    QDialog(parent),
    ui(new Ui::SimulatorDialog)
{
    ui->setupUi(this);
}

SimulatorDialog::~SimulatorDialog()
{
    delete ui;
}
